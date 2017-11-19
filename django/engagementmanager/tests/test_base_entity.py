#
# ============LICENSE_START==========================================
# org.onap.vvp/engagementmgr
# ===================================================================
# Copyright © 2017 AT&T Intellectual Property. All rights reserved.
# ===================================================================
#
# Unless otherwise specified, all software contained herein is licensed
# under the Apache License, Version 2.0 (the “License”);
# you may not use this software except in compliance with the License.
# You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Unless otherwise specified, all documentation contained herein is licensed
# under the Creative Commons License, Attribution 4.0 Intl. (the “License”);
# you may not use this documentation except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://creativecommons.org/licenses/by/4.0/
#
# Unless required by applicable law or agreed to in writing, documentation
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ============LICENSE_END============================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from abc import ABCMeta, abstractmethod
import http.client
import inspect
import re
import django
from engagementmanager.tests.vvpEntitiesCreator import VvpEntitiesCreator
from engagementmanager.service.logging_service import LoggingServiceFactory
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
import psycopg2
from rest_framework.parsers import JSONParser
from wheel.signatures import assertTrue
django.setup()

logger = LoggingServiceFactory.get_logger()


class TestBaseEntity(TestCase):
    __metaclass__ = ABCMeta

    def setUp(self):
        logger.debug("---------------------- TestCase " +
                     self.__class__.__name__ + " ----------------------")
        self.urlPrefix = "/%s/v1/engmgr/" % settings.PROGRAM_NAME_URL_PREFIX
        self.conn = http.client.HTTPConnection(
            "127.0.0.1", 8000)  # @UndefinedVariable
        self.c = Client()
        self.creator = VvpEntitiesCreator()
        settings.IS_SIGNAL_ENABLED = False
        self.childSetup()

    def tearDown(self):
        settings.IS_SIGNAL_ENABLED = True
        self.conn.close()
        logger.debug("----------------------  TestCase " +
                     self.__class__.__name__ + " ---------------------- ")
        logger.debug("")
        logger.debug("")

    def createVendors(self, vendorList):
        for vendor in vendorList:
            vendorUuid, vendor = self.creator.createVendor(vendor)
            logger.debug(vendorUuid)

    def createDefaultRoles(self):
        # Create Default Roles if does not exist
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()

    def printTestName(self, testNameTrigger):
        if testNameTrigger == "START":
            logger.debug("[TestName: " + inspect.stack()[1][3] + " - START]")
        elif testNameTrigger == "END":
            logger.debug("[TestName: " + inspect.stack()[1][3] + " - END]")

    @abstractmethod
    def childSetup(self):
        pass

    def nativeConnect2Db(self):
        return psycopg2.connect(
            "dbname='icedb' user='iceuser' host='localhost' \
            password='Aa123456' port='5433'")

    def deleteRecord(self, urlStr, getRecord, isNegativeTest):
        logger.debug("DELETE: " + urlStr + "/" + getRecord)
        self.conn.request("DELETE", urlStr + "/" + getRecord)
        r1 = self.conn.getresponse()
        logger.debug("DELETE response status code: " + str(r1.status))
        if (not isNegativeTest):
            assertTrue(r1.status == 204)
            return r1
        elif (isNegativeTest):
            return r1

    def createEntityViaPost(self, urlStr, params, headers=None):
        logger.debug("POST: " + urlStr + " Body: " +
                     params + " Headers: " + str(headers))
        self.conn.request("POST", urlStr, params, headers)
        r1 = self.conn.getresponse()
        return r1

    def editEntityViaPut(self, urlStr, getRecord, params, isNegativeTest):
        logger.debug("PUT: " + urlStr + "/" + getRecord + " " + params)
        self.conn.request("PUT", urlStr + "/" + getRecord, params)
        r1 = self.conn.getresponse()
        logger.debug("PUT response status code: " + str(r1.status))
        if (not isNegativeTest):
            assertTrue(r1.status == 200)
            return r1
        elif (isNegativeTest):
            return r1

    '''
    If you wish to "SELECT *" and get the first record then send
    queryFilterName=1 and queryFilterValue=1 to the method
    '''

    def filterTableByColAndVal(
            self,
            queryColumnName,
            queryTableName,
            queryFilterName,
            queryFilterValue):
        dbConn = self.nativeConnect2Db()
        cur = dbConn.cursor()
        queryStr = "SELECT %s FROM %s WHERE %s ='%s'" % (
            queryColumnName, queryTableName, queryFilterName, queryFilterValue)
        logger.debug(queryStr)
        cur.execute(queryStr)
        result = str(cur.fetchone())
        if (bool(re.search('[^0-9]', result))):
            logger.debug(
                "Looks like result (" +
                result +
                ") from DB is in a multi column pattern: \
                [col1, col2,...,coln], omitting it all colm beside " +
                queryColumnName)
            if (result.find("',)") != -1):  # formatting strings e.g uuid
                result = result.partition('\'')[-1].rpartition('\'')[0]
            elif (result.find(",)") != -1):  # formatting ints e.g id
                result = result.partition('(')[-1].rpartition(',')[0]
        logger.debug("Filter result: " + result)
        return result

    def selectLastValue(self, queryColumnName, queryTableName, orderBy="id"):
        dbConn = self.nativeConnect2Db()
        cur = dbConn.cursor()
        queryStr = "select %s from %s ORDER BY %s DESC LIMIT 1;" % (
            queryColumnName, queryTableName, orderBy)
        logger.debug(queryStr)
        cur.execute(queryStr)
        result = str(cur.fetchone())
        if (bool(re.search('[^0-9]', result))):
            logger.debug(
                "Looks like result (" +
                result +
                ") from DB is in a multi column pattern: [col1, col2,...,coln]\
                , omitting it all colm beside " +
                queryColumnName)
            if (result.find("',)") != -1):  # formatting strings e.g uuid
                result = result.partition('\'')[-1].rpartition('\'')[0]
            elif (result.find(",)") != -1):  # formatting ints e.g id
                result = result.partition('(')[-1].rpartition(',')[0]
        logger.debug("Filter result: " + result)
        return result

    def columnMaxLength(self, tableName, columnName):
        dbConn = self.nativeConnect2Db()
        cur = dbConn.cursor()
        queryStr = "SELECT character_maximum_length from \
        information_schema.columns WHERE table_name ='%s' \
        and column_name = '%s'" % (
            tableName, columnName)
        cur.execute(queryStr)
        result = str(cur.fetchone())
        if (bool(re.search('[^0-9]', result))):
            if (result.find("',)") != -1):  # formatting strings e.g uuid
                result = result.partition('\'')[-1].rpartition('\'')[0]
            elif (result.find(",)") != -1):  # formatting ints e.g id
                result = result.partition('(')[-1].rpartition(',')[0]
        return int(result)

    def getNumOfRecordViaRest(self, urlStr):
        logger.debug("GET: " + urlStr)
        self.conn.request("GET", urlStr)
        data_list = JSONParser().parse(self.conn.getresponse())
        cnt = str(len(data_list))
        return cnt

    def getMaximalNameValue(self, urlStr):
        logger.debug("GET: " + urlStr)
        self.conn.request("GET", urlStr)
        data_list = JSONParser().parse(self.conn.getresponse())
        maxName = 0
        for asi in data_list:
            logger.debug(asi)
            for key, value in asi.items():
                if (key == "name"):
                    if (maxName < int(value)):
                        maxName = int(value)
        logger.debug("MaximalNameValue=" + str(maxName))
        return maxName

    def getRecordAndDeserilizeIt(
            self, urlStr, getFilter, serializer, isCreateObj):
        logger.debug("GET: " + urlStr + "/" + getFilter)
        try:
            self.conn.request("GET", urlStr + "/" + getFilter)
            data = JSONParser().parse(self.conn.getresponse())
            logger.debug("DATA After JSON Parse:" + str(data))
            ser = serializer(data=data)
#             logger.debug(" --> Serializer data: "+repr(ser))
            if (isCreateObj):
                logger.debug("Creating ...")
                obj = ser.create(data)
            else:
                logger.debug("Updating ...")
                obj = ser.create(data)
                ser.update(obj, data)
        except Exception:
            logger.debug(Exception)
            raise Exception
        return obj

    def newParameters(self, oldValue, newValue, uuidValue):
        # Find and replace in string.
        newParams = re.sub(oldValue, newValue, self.params)
        newParams = re.sub("}", ', "uuid":"' + uuidValue +
                           '"}', newParams)  # Add UUID to params
        return newParams

    def negativeTestPost(self, getFilter, allowTwice=False):
        logger.debug("POST negative tests are starting now!")
        if (not allowTwice):
            logger.debug("Negative 01: Insert the same record twice via REST")
            r1 = self.createEntityViaPost(self.urlStr, self.params)
            logger.debug(r1.status, r1.reason)
            assertTrue(r1.status == 400)
            self.deleteRecord(self.urlStr, getFilter, False)
        logger.debug("Negative 02: Insert record with empty value via REST")
        # Create params with empty values.
        paramsEmptyValue = re.sub(r':\".*?\"', ':\"\"', self.params)
        r1 = self.createEntityViaPost(self.urlStr, paramsEmptyValue)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 400)
        logger.debug("Negative 03: Insert record with missing value via REST")
        # Create params without records part 1.
        paramsMissingValue = re.sub(r'{\".*?\":', '{\"\":', self.params)
        # Create params without records part 2.
        paramsMissingValue = re.sub(
            r', \".*?\":', ', \"\":', paramsMissingValue)
        r1 = self.createEntityViaPost(self.urlStr, paramsMissingValue)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 400)
        logger.debug("Negative 04: Insert record with more than " +
                     str(self.longValueLength) + " chars via REST")
        paramsLongValue = re.sub(r':\".*?\"',
                                 ':\"' + str(
                                     self.randomGenerator(
                                         "randomNumber",
                                         self.longValueLength)) + '\"',
                                 self.params)
        r1 = self.createEntityViaPost(self.urlStr, paramsLongValue)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 400)
        if (allowTwice):
            logger.debug("Deleting record from database...")
            self.deleteRecord(self.urlStr, getFilter, False)

    def negativeTestPut(self, getFilter, params):
        logger.debug("PUT negative tests are starting now!")
        # Check if getFilter contains non-digit characters.
        match = re.search("\D", getFilter)
        if not match:
            logger.debug("Negative 01: Edit non existing record via REST")
            nonExistingValue = self.randomGenerator("randomNumber", 5)
            r1 = self.editEntityViaPut(
                self.urlStr, nonExistingValue, params, True)
            logger.debug(r1.status, r1.reason)
            assertTrue(r1.status == 404)
            logger.debug(
                "Negative 02: Edit record with string \
                in URL instead of integer via REST")
            randStr = self.randomGenerator("randomString")
            r1 = self.editEntityViaPut(self.urlStr, randStr, params, True)
            logger.debug(r1.status, r1.reason)
            assertTrue(r1.status == 400)
        else:
            logger.debug("Negative 01: Edit non existing record via REST")
            nonExistingValue = self.randomGenerator("randomString")
            r1 = self.editEntityViaPut(
                self.urlStr, nonExistingValue, params, True)
            logger.debug(r1.status, r1.reason)
            assertTrue(r1.status == 404)
        logger.debug("Negative 02: Edit record without URL pointer via REST")
        r1 = self.editEntityViaPut(self.urlStr, "", params, True)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 405)
        logger.debug("Negative 03: Edit record with empty value via REST")
        # Create params with empty values.
        paramsEmptyValue = re.sub(r':\".*?\"', ':\"\"', params)
        r1 = self.editEntityViaPut(
            self.urlStr, getFilter, paramsEmptyValue, True)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 400)
        logger.debug("Negative 04: Edit record with missing value via REST")
        # Create params without records part 1.
        paramsMissingValue = re.sub(r'{\".*?\":', '{\"\":', params)
        # Create params without records part 2.
        paramsMissingValue = re.sub(
            r', \".*?\":', ', \"\":', paramsMissingValue)
        r1 = self.editEntityViaPut(
            self.urlStr, getFilter, paramsMissingValue, True)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 400)
        logger.debug("Deleting record from database...")
        self.deleteRecord(self.urlStr, getFilter, False)

    def negativeTestDelete(self):
        logger.debug("DELETE negative tests are starting now!")
        logger.debug(
            "Negative 01: Delete non existing record via \
            REST or wrong URL pointer")
        nonExistingValue = self.randomGenerator("randomString")
        r1 = self.deleteRecord(self.urlStr, nonExistingValue, True)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 404 or r1.status == 500 or r1.status == 400)
        logger.debug("Negative 02: Delete record without URL pointer via REST")
        r1 = self.deleteRecord(self.urlStr, "", True)
        logger.debug(r1.status, r1.reason)
        assertTrue(r1.status == 405)

    def failTest(self, failureReason):
        logger.debug(">>> Test failed!\n", failureReason)
        self.assertTrue(False)

    def failRestTest(self, r1):
        logger.debug(
            "Previous HTTP POST request has failed with " + str(r1.status))
        self.assertTrue(False)

    def randomGenerator(self, typeOfValue, numberOfDigits=0):
        return self.creator.randomGenerator(typeOfValue, numberOfDigits)

    def loginAndCreateSessionToken(self, user):
        return self.creator.loginAndCreateSessionToken(user)
