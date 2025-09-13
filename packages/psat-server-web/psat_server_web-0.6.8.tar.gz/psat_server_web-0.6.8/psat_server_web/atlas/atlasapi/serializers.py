import datetime
import re
import json
import requests
from django.db import IntegrityError
from django.db import connection
from datetime import datetime
from gkutils.commonutils import coneSearchHTM, FULL, QUICK, COUNT, CAT_ID_RA_DEC_COLS, base26, Struct
from rest_framework import serializers
import sys
from atlas.apiutils import candidateddcApi, getObjectList
from atlas.apiutils import getVRAScoresList
from atlas.apiutils import getVRATodoList
from atlas.apiutils import getCustomListObjects
from atlas.apiutils import getVRARankList
from atlas.apiutils import getExternalCrossmatchesList
from django.core.exceptions import ObjectDoesNotExist

# 2024-01-29 KWS Need the model to do inserts.
from atlas.models import TcsVraScores
from atlas.models import AtlasDiffObjects
from atlas.models import TcsVraTodo
from atlas.models import TcsObjectGroups
from atlas.models import TcsObjectGroupDefinitions
from atlas.models import TcsVraRank
from atlas.models import TcsCrossMatchesExternal

#CAT_ID_RA_DEC_COLS['objects'] = [['objectId', 'ramean', 'decmean'], 1018]

REQUEST_TYPE_CHOICES = (
    ('count', 'Count'),
    ('all', 'All'),
    ('nearest', 'Nearest'),
)


class ConeSerializer(serializers.Serializer):
    ra = serializers.FloatField(required=True)
    dec = serializers.FloatField(required=True)
    radius = serializers.FloatField(required=True)
    requestType = serializers.ChoiceField(choices=REQUEST_TYPE_CHOICES)

    def save(self):

        ra = self.validated_data['ra']
        dec = self.validated_data['dec']
        radius = self.validated_data['radius']
        requestType = self.validated_data['requestType']

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user

        if radius > 300:
            replyMessage = "Max radius is 300 arcsec."
            info = {"error": replyMessage}
            return info

        replyMessage = 'No object found ra=%.5f dec=%.5f radius=%.2f' % (ra, dec, radius)
        info = {"error": replyMessage}

        # Is there an object within RADIUS arcsec of this object? - KWS - need to fix the gkhtm code!!
        # For ATLAS QUICK does not work because of the `dec` syntax error problem. Use FULL until I figure out what
        # needs to be fixed.
        message, results = coneSearchHTM(ra, dec, radius, 'atlas_diff_objects', queryType=FULL, conn=connection, django=True)

        obj = None
        separation = None

        objectList = []
        if requestType == "nearest":
            if len(results) > 0:
                obj = results[0][1]['id']
                separation = results[0][0]
                objName = results[0][1]['atlas_designation']
                info = {"object": obj, "separation": separation, "objectname": objName}
            else:
                info = {}
        if requestType == "all":
            for row in results:
                objectList.append({"object": row[1]["id"], "separation": row[0], "objectname": row[1]["atlas_designation"]})
            info = objectList
        if requestType == "count":
            info = {'count': len(results)}

        return info


class ObjectsSerializer(serializers.Serializer):
    objects = serializers.CharField(required=True)
    mjd = serializers.FloatField(required=False, default=None)

    def save(self):
        objects = self.validated_data['objects']
        mjd = self.validated_data['mjd']

        olist = []
        for tok in objects.split(','):
            olist.append(tok.strip())

        if len(olist) > 100:
            return {"info": "Max number of objects for each requests is 100"}
#        olist = olist[:10] # restrict to 10

        # Get the authenticated user, if it exists.
        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = request.user


        result = []
        for candidate in olist:
            result.append(candidateddcApi(request, candidate, mjdThreshold=mjd))
        return result


class ObjectListSerializer(serializers.Serializer):
    objectlistid = serializers.IntegerField(required=True)
    getcustomlist = serializers.BooleanField(required=False, default = False)
    datethreshold = serializers.DateTimeField(required=False, default=None)

    def save(self):
        objectlistid = self.validated_data['objectlistid']
        getcustomlist = self.validated_data['getcustomlist']
        datethreshold = self.validated_data['datethreshold']

        request = self.context.get("request")

        dateThreshold = None
        if datethreshold is not None:
            dateThreshold = self.validated_data['datethreshold']

        objectList = getObjectList(request, objectlistid, getCustomList = getcustomlist, dateThreshold = dateThreshold)
        return objectList


# 2024-01-17 KWS Insert a VRA row for an object. For the time being do this one at a time.
# 2024-02-21 KWS Changed required to False for all three prob values.
class VRAScoresSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    preal = serializers.FloatField(required=False, default=None)
    pgal = serializers.FloatField(required=False, default=None)
    pfast = serializers.FloatField(required=False, default=None)
    # 2024-08-14 KWS Added 3 new values to the form for Rank.
    rank = serializers.FloatField(required=False, default=None)
    rank_alt1 = serializers.FloatField(required=False, default=None)
    is_gal_cand = serializers.IntegerField(required=False, default=None)
    debug = serializers.BooleanField(required=False, default=False)
    insertdate = serializers.DateTimeField(required=False, default=None)


    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        preal = self.validated_data['preal']
        pgal = self.validated_data['pgal']
        pfast = self.validated_data['pfast']
        rank = self.validated_data['rank']
        rank_alt1 = self.validated_data['rank_alt1']
        is_gal_cand = self.validated_data['is_gal_cand']
        insertdate = self.validated_data['insertdate']
        debug = self.validated_data['debug']

        insertDate = None
        if insertdate is not None:
            insertDate = self.validated_data['insertdate']

        replyMessage = 'Row created.'

        userId = 'unknown'
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            userId = str(request.user)

        if not insertDate:
            insertDate = datetime.now()

        data = {'transient_object_id_id': objectid,
                'preal': preal,
                'pgal': pgal,
                'pfast': pfast,
                'rank': rank,
                'rank_alt1': rank_alt1,
                'is_gal_cand': is_gal_cand,
                'timestamp': insertDate,
                'debug': debug,
                'apiusername': userId}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        ## Does the VRA row exist?
        #vra = None
        #try:
        #    vra = TcsVraScores.objects.get(transient_object_id_id=objectid, debug=debug)
        
        #except ObjectDoesNotExist as e:
        #    # That's OK - we'll create a new object
        #    pass
        
        #if vra:
        #    instance = vra
        #else:
        instance = TcsVraScores(**data)
        #try:

        #    if vra is not None:
        #        instance.preal = preal
        #        instance.pfast = pfast
        #        instance.pgal = pgal
        #        instance.timestamp = insertDate
        #        i = instance.save()
        #    else:
        i = instance.save()

        #except IntegrityError as e:
        #    replyMessage = 'Duplicate row. Cannot add row.'

        info = { "objectid": objectid, "info": replyMessage }
        return info



class VRAScoresListSerializer(serializers.Serializer):
    objects = serializers.CharField(required=False, default=None)
    debug = serializers.BooleanField(required=False, default=False)
    datethreshold = serializers.DateTimeField(required=False, default='1970-01-01')
    idthreshold = serializers.IntegerField(required=False, default=0)

    def save(self):
        objects = self.validated_data['objects']
        datethreshold = self.validated_data['datethreshold']
        debug = self.validated_data['debug']
        idthreshold = self.validated_data['idthreshold']

        request = self.context.get("request")

        olist = []

        if objects is not None:
            for tok in objects.split(','):
                olist.append(tok.strip())

        vraScoresList = getVRAScoresList(request, objects = olist, debug = debug, dateThreshold = datethreshold, idThreshold = idthreshold)
        return vraScoresList


# 2024-02-21 KWS Changed required to False for all three prob values.
class VRATodoSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    insertdate = serializers.DateTimeField(required=False, default=None)

    import sys

    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        insertdate = self.validated_data['insertdate']

        insertDate = None
        if insertdate is not None:
            insertDate = self.validated_data['insertdate']

        replyMessage = 'Row created.'

        if not insertDate:
            insertDate = datetime.now()

        data = {'transient_object_id_id': objectid,
                'timestamp': insertDate}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        try:
            instance = TcsVraTodo(**data)
            i = instance.save(force_insert=True)
            # NOTE: Inserting an object by setting the primary key actually REPLACES the object. Do we want this behaviour??
            #       The integrity error below never happens because I've now set the model with primary_key=True.
            #       To fix this I've added force_insert = True above.
        except IntegrityError as e:
            replyMessage = 'Duplicate row. Cannot add row.'

        info = { "objectid": objectid, "info": replyMessage }
        return info


class VRATodoListSerializer(serializers.Serializer):
    objects = serializers.CharField(required=False, default=None)
    datethreshold = serializers.DateTimeField(required=False, default='1970-01-01')
    idthreshold = serializers.IntegerField(required=False, default=0)

    def save(self):
        objects = self.validated_data['objects']
        datethreshold = self.validated_data['datethreshold']
        idthreshold = self.validated_data['idthreshold']

        request = self.context.get("request")

        olist = []

        if objects is not None:
            for tok in objects.split(','):
                olist.append(tok.strip())

        vraTodoList = getVRATodoList(request, objects = olist, dateThreshold = datethreshold, idThreshold = idthreshold)
        return vraTodoList


# 2024-02-21 KWS Changed required to False for all three prob values.
class TcsObjectGroupsSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    objectgroupid = serializers.IntegerField(required=True)

    import sys

    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        objectGroupId = self.validated_data['objectgroupid']

        replyMessage = 'Row created.'

        # This is what gets inserted into the database.
        data = {'transient_object_id_id': objectid,
                'object_group_id': objectGroupId}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        try:
            group = TcsObjectGroupDefinitions.objects.get(pk=objectGroupId)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object group ID does not exist.'
            info = { "objectgroupid": objectGroupId, "info": replyMessage }
            return info

        try:
            instance = TcsObjectGroups(**data)
            i = instance.save(force_insert=True)
            # NOTE: Inserting an object by setting the primary key actually REPLACES the object. Do we want this behaviour??
            #       The integrity error below never happens because I've now set the model with primary_key=True.
            #       To fix this I've added force_insert = True above.
        except IntegrityError as e:
            replyMessage = 'Duplicate row. Cannot add row.'

        info = { "objectgroupid": objectid, "info": replyMessage }
        return info

# 2024-02-21 KWS Changed required to False for all three prob values.
class TcsObjectGroupsDeleteSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    objectgroupid = serializers.IntegerField(required=True)

    import sys

    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        objectGroupId = self.validated_data['objectgroupid']

        replyMessage = 'Row deleted.'

        # This is what gets inserted into the database.
        data = {'transient_object_id_id': objectid,
                'object_group_id': objectGroupId}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        try:
            group = TcsObjectGroupDefinitions.objects.get(pk=objectGroupId)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object group ID does not exist.'
            info = { "objectgroupid": objectGroupId, "info": replyMessage }
            return info

        try:
            instance = TcsObjectGroups.objects.get(transient_object_id__id = objectid, object_group_id = objectGroupId)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object group ID does not exist or object ID does not exist.'
            info = { "objectgroupid": objectGroupId, "objectid": objectid, "info": replyMessage }
            return info

        i = instance.delete()
        #replyMessage = 'Duplicate row. Cannot add row.'

        info = { "objectgroupid": objectid, "info": replyMessage }
        return info

class TcsObjectGroupsListSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=False, default=None)
    objectgroupid = serializers.IntegerField(required=False, default=None)

    def save(self):
        objectid = self.validated_data['objectid']
        objectGroupId = self.validated_data['objectgroupid']

        request = self.context.get("request")

        customListObjects = getCustomListObjects(request, objectid, objectGroupId)
        return customListObjects


# 2024-05-22 KWS Added VRARank and VRARankList Serializers.
class VRARankSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    rank = serializers.FloatField(required=True)
    rank_alt1 = serializers.FloatField(required=False, default=None)
    is_gal_cand = serializers.IntegerField(required=False, default=None)
    insertdate = serializers.DateTimeField(required=False, default=None)

    import sys

    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        insertdate = self.validated_data['insertdate']
        rank = self.validated_data['rank']
        rank_alt1 = self.validated_data['rank_alt1']
        is_gal_cand = self.validated_data['is_gal_cand']

        insertDate = None
        if insertdate is not None:
            insertDate = self.validated_data['insertdate']

        replyMessage = 'Row created.'

        if not insertDate:
            insertDate = datetime.now()

        data = {'transient_object_id_id': objectid,
                'rank': rank,
                'rank_alt1': rank_alt1,
                'is_gal_cand': is_gal_cand,
                'timestamp': insertDate}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        try:
            instance = TcsVraRank(**data)
            # Do not use force_insert=True here. We really want to update any existing row
            # or insert if the row doesn't exist.
            i = instance.save()

        except IntegrityError as e:
            # Should never happen!
            sys.stderr.write(str(e))
            replyMessage = 'Duplicate row. Cannot add row.'

        info = { "objectid": objectid, "info": replyMessage }
        return info


class VRARankListSerializer(serializers.Serializer):
    objects = serializers.CharField(required=False, default=None)
    datethreshold = serializers.DateTimeField(required=False, default='1970-01-01')

    def save(self):
        objects = self.validated_data['objects']
        datethreshold = self.validated_data['datethreshold']

        request = self.context.get("request")

        olist = []

        if objects is not None:
            for tok in objects.split(','):
                olist.append(tok.strip())

        vraRankList = getVRARankList(request, objects = olist, dateThreshold = datethreshold)
        return vraRankList

# 2024-09-24 KWS Added tcs_cross_matches_external viewer. We want to extract any ATLAS objects associated
#                with any named external courses.

class ExternalCrossmatchesListSerializer(serializers.Serializer):
    # We could send ATLAS IDs or any external crossmatch IDs, like TNS names.
    externalObjects = serializers.CharField(required=False, default=None)

    def save(self):
        externalObjects = self.validated_data['externalObjects']

        request = self.context.get("request")

        olist = []

        if externalObjects is not None:
            for tok in externalObjects.split(','):
                olist.append(tok.strip())

        externalCrossmatchesList = getExternalCrossmatchesList(request, externalObjects = olist)
        return externalCrossmatchesList

# 2024-09-24 KWS Added new serializer to updated the detection_list_id of an object in order
#                to be able to "snooze" and "unsnooze" it. We'll use the possible list as
#                snooze list.
class ObjectDetectionListSerializer(serializers.Serializer):
    objectid = serializers.IntegerField(required=True)
    # Only allow the object list to be updated
    objectlist = serializers.IntegerField(required=True)
    # Updates the date_modified field for an object too.
    insertdate = serializers.DateTimeField(required=False, default=None)

    import sys

    def save(self):

        from django.conf import settings
        objectid = self.validated_data['objectid']
        objectlist = self.validated_data['objectlist']
        insertdate = self.validated_data['insertdate']

        insertDate = None
        if insertdate is not None:
            insertDate = self.validated_data['insertdate']

        replyMessage = 'Row created.'

        if not insertDate:
            insertDate = datetime.now()

        data = {'detection_list_id_id': objectlist,
                'date_modified': insertDate}

        # Does the objectId actually exit - not allowed to comment on objects that don't exist!
        # This should really return a 404 message.
        try:
            transient = AtlasDiffObjects.objects.get(pk=objectid)
        except ObjectDoesNotExist as e:
            replyMessage = 'Object does not exist.'
            info = { "objectid": objectid, "info": replyMessage }
            return info

        try:
            for key, value in data.items():
                sys.stderr.write("\nkey=%s\n" % key)
                sys.stderr.write("\nvalue=%s\n" % value)
                if key=='detection_list_id_id' and value not in (3,4,12):
                    replyMessage = 'Error updating row.'
                    info = { "objectid": objectid, "info": replyMessage }
                    return info
                else:
                    setattr(transient, key, value)
            transient.save()

        except IntegrityError as e:
            replyMessage = 'Error updating row.'

        info = { "objectid": objectid, "info": replyMessage }
        return info

