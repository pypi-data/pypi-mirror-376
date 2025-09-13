# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" data fetch thread """

from __future__ import print_function
from __future__ import unicode_literals

from pyqtgraph import QtCore
import time
import logging

from .omniQThread import OmniQThread

#: (:obj:`float`) refresh time in seconds
GLOBALREFRESHTIME = .1
#: (:obj:`bool`) auto enlarge time
GLOBALAUTOREFRESHTIME = True

logger = logging.getLogger("lavue")


class ExchangeList(object):

    """  subclass for data caching """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`list` <:obj:`str`, :class:`numpy.ndarray`, :obj:`str` >)
        #:      exchange object
        self.__elist = [None, None, None]
        #: (:obj:`pyqtgraph.QtCore.QMutex`) mutex lock
        self.__mutex = QtCore.QMutex()

    def addData(self, name, data, metadata=""):
        """ write data into exchange object

        :param name: image name
        :type name: :obj:`str`
        :param data: image data
        :type data: :class:`numpy.ndarray`
        :param metadata: json dictionary with image metadata
        :type metadata: :obj:`str`
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__elist[0] = name
            self.__elist[1] = data
            self.__elist[2] = metadata

    def readData(self):
        """ read data from exchange object

        :returns: tuple of exchange object (name, data, metadata)
        :rtype: :obj:`list` <:obj:`str`, :class:`numpy.ndarray`, :obj:`str` >
        """
        with QtCore.QMutexLocker(self.__mutex):
            a, b, c = self.__elist[0], self.__elist[1], self.__elist[2]
        return a, b, c


# subclass for threading
class DataFetchThread(OmniQThread):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) new data name signal
    newDataNameFetched = QtCore.pyqtSignal(str, str)

    def __init__(self, datasource, alist, tid=0):
        """ constructor

        :param datasource: image source
        :type datasource: :class:`lavuelib.imageSource.BaseSource`
        :param alist: exchange object
        :type alist: :class:`ExchangeList`
        """
        OmniQThread.__init__(self)
        #: (:class:`lavuelib.imageSource.BaseSource`) image source
        self.__datasource = datasource
        #: (:class:`ExchangeList`) exchange list
        self.__list = alist
        #: (:obj:`bool`) connection flag
        self.__isConnected = False
        #: (:obj:`bool`) execute loop flag
        self.__loop = False
        #: (:obj:`bool`) ready flag
        self.__ready = True
        #: (:obj:`int`) thread id
        self.__tid = tid
        #: (:class:`pyqtgraph.QtCore.QMutex`) thread mutex
        self.__mutex = QtCore.QMutex()
        #: (:obj:`int`) current timestamp
        self.__tm = time.time()
        #: (:obj:`int`) current timestamp
        self.__tm2 = time.time()
        #: (:obj:`int`) current timestamp
        self.__dt = 0
        #: (:obj:`int`) counter
        self.__counter = 0
        #: (:obj:`int`) maximal counter value
        self.__maxcounter = 100
        #: (:obj:`int`) start time
        self.__starttime = 0
        #: (:obj:`float`) elapsed time factor
        self.__factor = 2.0

    def _run(self):
        """ run function of the fetching thread
        """
        global GLOBALREFRESHTIME
        self.__loop = True
        self.__dt = 0
        skip = False
        while self.__loop:
            if not self.__isConnected:
                self.msleep(int(1000*GLOBALREFRESHTIME))
            if skip:
                self.msleep(int(100*GLOBALREFRESHTIME))
            else:
                for _ in range(3):
                    self.msleep(
                        max(int((1000*GLOBALREFRESHTIME - self.__dt)/4.), 0))
            self.msleep(
                max(int(
                    1000*GLOBALREFRESHTIME
                    - (time.time() - self.__tm) * 1000.), 0))
            self.__tm = time.time()
            if self.__isConnected and self.__ready:
                try:
                    with QtCore.QMutexLocker(self.__mutex):
                        img, name, metadata = self.__datasource.getData()
                    if not self.__tid and GLOBALAUTOREFRESHTIME:
                        if not self.__counter:
                            self.__starttime = self.__tm
                        if self.__counter == self.__maxcounter:
                            etime = time.time()
                            if self.__starttime:
                                eltime = float(etime - self.__starttime) \
                                    / self.__maxcounter
                                # print(eltime, GLOBALREFRESHTIME)
                                if eltime > self.__factor * GLOBALREFRESHTIME:
                                    GLOBALREFRESHTIME = GLOBALREFRESHTIME * \
                                        self.__factor
                                    logger.warning(
                                        "The Image refresh time changed to: "
                                        "%s s" % GLOBALREFRESHTIME)
                            self.__counter = 0
                        else:
                            self.__counter += 1
                except Exception as e:
                    name = "__ERROR__"
                    img = str(e)
                    metadata = ""
                if name is not None:
                    self.__list.addData(name, img, metadata)
                    self.__ready = False
                    # print(self.__tid, "ADDED", time.time())
                    self.newDataNameFetched.emit(name, metadata)
                else:
                    self.__ready = True
                skip = False
            else:
                skip = True
            self.__tm2 = time.time()
            self.__dt = (self.__tm2 - self.__tm) * 1000.
            # print("END", self.__tid, self.__dt)

    @QtCore.pyqtSlot(bool)
    def changeStatus(self, status):
        """ change connection status

        :param status: connection status
        :type status: :obj:`bool`
        """
        self.__isConnected = status
        self.__ready = True

    def setTimeStamp(self, tmstamp):
        """ set time stamp

        :param tmstamp: set timestamp
        :type tmstamp: :obj:`int`
        """
        self.__tm = tmstamp
        self.__dt = (self.__tm2 - self.__tm+0.0010) * 1000.

    def getTimeStamp(self):
        """ get time stamp

        :returns: time stamp
        :rtype: :obj:`int`
        """
        return self.__tm

    def setDataSource(self, datasource):
        """ sets datasource
        :param datasource: datasource object
        :type datasource: :class:`lavuelib.imageSource.BaseSource`
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__datasource = datasource

    def ready(self):
        """ continue acquisition
        """
        self.__ready = True

    def fetching(self):
        """ provides read flag
        """
        return not self.__ready

    def stop(self):
        """ stop the thread
        """
        self.__isConnected = False
        self.__ready = True
        self.__loop = False

    def isFetching(self):
        """ is datasource source connected

        :returns: if datasource source connected
        :rtype: :obj:`bool`
        """
        return self.__loop
