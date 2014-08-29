from lxml import etree

import logging
log = logging.getLogger(__name__)


class MappedXmlObject(object):
    elements = []


class MappedXmlDocument(MappedXmlObject):
    def __init__(self, xml_str=None, xml_tree=None):
        assert (xml_str or xml_tree is not None), 'Must provide some XML in one format or another'
        self.xml_str = xml_str
        self.xml_tree = xml_tree

    def read_values(self):
        '''For all of the elements listed, finds the values of them in the
        XML and returns them.'''
        values = {}
        tree = self.get_xml_tree()
        for element in self.elements:
            values[element.name] = element.read_value(tree)
        self.infer_values(values)
        return values

    def read_value(self, name):
        '''For the given element name, find the value in the XML and return
        it.
        '''
        tree = self.get_xml_tree()
        for element in self.elements:
            if element.name == name:
                return element.read_value(tree)
        raise KeyError

    def get_xml_tree(self):
        if self.xml_tree is None:
            parser = etree.XMLParser(remove_blank_text=True)
            if type(self.xml_str) == unicode:
                xml_str = self.xml_str.encode('utf8')
            else:
                xml_str = self.xml_str
            self.xml_tree = etree.fromstring(xml_str, parser=parser)
        return self.xml_tree

    def infer_values(self, values):
        pass


class MappedXmlElement(MappedXmlObject):
    namespaces = {}

    def __init__(self, name, search_paths=[], multiplicity="*", elements=[]):
        self.name = name
        self.search_paths = search_paths
        self.multiplicity = multiplicity
        self.elements = elements or self.elements

    def read_value(self, tree):
        values = []
        for xpath in self.get_search_paths():
            elements = self.get_elements(tree, xpath)
            values = self.get_values(elements)
            if values:
                break
        return self.fix_multiplicity(values)

    def get_search_paths(self):
        if type(self.search_paths) != type([]):
            search_paths = [self.search_paths]
        else:
            search_paths = self.search_paths
        return search_paths

    def get_elements(self, tree, xpath):
        return tree.xpath(xpath, namespaces=self.namespaces)

    def get_values(self, elements):
        values = []
        if len(elements) == 0:
            pass
        else:
            for element in elements:
                value = self.get_value(element)
                values.append(value)
        return values

    def get_value(self, element):
        if self.elements:
            value = {}
            for child in self.elements:
                value[child.name] = child.read_value(element)
            return value
        elif type(element) == etree._ElementStringResult:
            value = str(element)
        elif type(element) == etree._ElementUnicodeResult:
            value = unicode(element)
        else:
            value = self.element_tostring(element)
        return value

    def element_tostring(self, element):
        return etree.tostring(element, pretty_print=False)

    def fix_multiplicity(self, values):
        '''
        When a field contains multiple values, yet the spec says
        it should contain only one, then return just the first value,
        rather than a list.

        In the ISO19115 specification, multiplicity relates to:
        * 'Association Cardinality'
        * 'Obligation/Condition' & 'Maximum Occurence'
        '''
        if self.multiplicity == "0":
            # 0 = None
            if values:
                log.warn("Values found for element '%s' when multiplicity should be 0: %s",  self.name, values)
            return ""
        elif self.multiplicity == "1":
            # 1 = Mandatory, maximum 1 = Exactly one
            if not values:
                log.warn("Value not found for element '%s'" % self.name)
                return ''
            return values[0]
        elif self.multiplicity == "*":
            # * = 0..* = zero or more
            return values
        elif self.multiplicity == "0..1":
            # 0..1 = Mandatory, maximum 1 = optional (zero or one)
            if values:
                return values[0]
            else:
                return ""
        elif self.multiplicity == "1..*":
            # 1..* = one or more
            return values
        else:
            log.warning('Multiplicity not specified for element: %s',
                        self.name)
            return values


class ISOElement(MappedXmlElement):

    namespaces = {
       "gts": "http://www.isotc211.org/2005/gts",
       "gml": "http://www.opengis.net/gml/3.2",
       "gmx": "http://www.isotc211.org/2005/gmx",
       "gsr": "http://www.isotc211.org/2005/gsr",
       "gss": "http://www.isotc211.org/2005/gss",
       "gco": "http://www.isotc211.org/2005/gco",
       "gmd": "http://www.isotc211.org/2005/gmd",
       "srv": "http://www.isotc211.org/2005/srv",
       "xlink": "http://www.w3.org/1999/xlink",
       "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }


class ISOResourceLocator(ISOElement):
    #[SMR] relative to CI_OnlineResource

    elements = [
        ISOElement(
            name="url",
            search_paths=[
                "gmd:linkage/gmd:URL/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="function",
            search_paths=[
                "gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="name",
            search_paths=[
                "gmd:name/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="description",
            search_paths=[
                "gmd:description/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="protocol",
            search_paths=[
                "gmd:protocol/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ]


class ISOResponsibleParty(ISOElement):

    elements = [
        ISOElement(
            name="individual-name",
            search_paths=[
                "gmd:individualName/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="organisation-name",
            search_paths=[
                "gmd:organisationName/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="position-name",
            search_paths=[
                "gmd:positionName/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="contact-info",
            search_paths=[
                "gmd:contactInfo/gmd:CI_Contact",
            ],
            multiplicity="0..1",
            elements = [
                ISOElement(
                    name="email",
                    search_paths=[
                        "gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString/text()",
                    ],
                    multiplicity="0..1"),
                ISOElement(
                    name="telephone",
                    search_paths=[
                        "gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString/text()",
                    ],
                    multiplicity="0..1"
                ),
                ISOResourceLocator(
                    name="online-resource",
                    search_paths=[
                        "gmd:onlineResource/gmd:CI_OnlineResource",
                    ],
                    multiplicity="0..1",
                ),

            ]
        ),
        ISOElement(
            name="role",
            search_paths=[
                "gmd:role/gmd:CI_RoleCode/@codeListValue",
            ],
            multiplicity="0..1",
        ),
    ]

# omits amendmentNumber, specification, and fileDecompressionTechnique
class ISODataFormat(ISOElement):

    elements = [
        ISOElement(
            name="name",
            search_paths=[
                "gmd:name/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="version",
            search_paths=[
                "gmd:version/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
    ]


class ISOReferenceDate(ISOElement):

    elements = [
        ISOElement(
            name="type",
            search_paths=[
                "gmd:dateType/gmd:CI_DateTypeCode/@codeListValue",
                "gmd:dateType/gmd:CI_DateTypeCode/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="value",
            search_paths=[
                "gmd:date/gco:Date/text()",
                "gmd:date/gco:DateTime/text()",
            ],
            multiplicity="1",
        ),
    ]

class ISOCoupledResources(ISOElement):

    elements = [
        ISOElement(
            name="title",
            search_paths=[
                "@xlink:title",
            ],
            multiplicity="*",
        ),
        ISOElement(
            name="href",
            search_paths=[
                "@xlink:href",
            ],
            multiplicity="*",
        ),
        ISOElement(
            name="uuid",
            search_paths=[
                "@uuidref",
            ],
            multiplicity="*",
        ),

    ]


class ISOBoundingBox(ISOElement):

    elements = [
        ISOElement(
            name="west",
            search_paths=[
                "gmd:westBoundLongitude/gco:Decimal/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="east",
            search_paths=[
                "gmd:eastBoundLongitude/gco:Decimal/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="north",
            search_paths=[
                "gmd:northBoundLatitude/gco:Decimal/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="south",
            search_paths=[
                "gmd:southBoundLatitude/gco:Decimal/text()",
            ],
            multiplicity="1",
        ),
    ]

class ISOBrowseGraphic(ISOElement):

    elements = [
        ISOElement(
            name="file",
            search_paths=[
                "gmd:fileName/gco:CharacterString/text()",
            ],
            multiplicity="1",
        ),
        ISOElement(
            name="description",
            search_paths=[
                "gmd:fileDescription/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="type",
            search_paths=[
                "gmd:fileType/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
    ]


class ISOKeyword(ISOElement):

    elements = [
        ISOElement(
            name="keyword",
            search_paths=[
                "gmd:keyword/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        ISOElement(
            name="type",
            search_paths=[
                "gmd:type/gmd:MD_KeywordTypeCode/@codeListValue",
                "gmd:type/gmd:MD_KeywordTypeCode/text()",
            ],
            multiplicity="0..1",
        ),
        # If Thesaurus information is needed at some point, this is the
        # place to add it
        # SMR 2014-08-28, add thesaurus inforamation
   ]


class ISOUsage(ISOElement):

    elements = [
        ISOElement(
            name="usage",
            search_paths=[
                "gmd:specificUsage/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOResponsibleParty(
            name="contact-info",
            search_paths=[
                "gmd:userContactInfo/gmd:CI_ResponsibleParty",
            ],
            multiplicity="0..1",
        ),

   ]


class ISOAggregationInfo(ISOElement):

    elements = [
        ISOElement(
            name="aggregate-dataset-name",
            search_paths=[
                "gmd:aggregateDatasetName/gmd:CI_Citation/gmd:title/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="aggregate-dataset-identifier",
            search_paths=[
                "gmd:aggregateDatasetIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="association-type",
            search_paths=[
                "gmd:associationType/gmd:DS_AssociationTypeCode/@codeListValue",
                "gmd:associationType/gmd:DS_AssociationTypeCode/text()",
            ],
            multiplicity="0..1",
        ),
        ISOElement(
            name="initiative-type",
            search_paths=[
                "gmd:initiativeType/gmd:DS_InitiativeTypeCode/@codeListValue",
                "gmd:initiativeType/gmd:DS_InitiativeTypeCode/text()",
            ],
            multiplicity="0..1",
        ),
   ]


class ISODocument(MappedXmlDocument):

    # Attribute specifications from "XPaths for GEMINI" by Peter Parslow.

    elements = [
        #file identifier
        ISOElement(
            name="guid",
            search_paths="gmd:fileIdentifier/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        #metadata language
        ISOElement(
            name="metadata-language",
            search_paths=[
                "gmd:language/gmd:LanguageCode/@codeListValue",
                "gmd:language/gmd:LanguageCode/text()",
            ],
            multiplicity="0..1",
        ),
        #metadata standard name
        ISOElement(
            name="metadata-standard-name",
            search_paths="gmd:metadataStandardName/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        #metadata standard version
        ISOElement(
            name="metadata-standard-version",
            search_paths="gmd:metadataStandardVersion/gco:CharacterString/text()",
            multiplicity="0..1",
        ),
        #resource type from gmd:hierarchyLevel
        ISOElement(
            name="resource-type",
            search_paths=[
                "gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue",
                "gmd:hierarchyLevel/gmd:MD_ScopeCode/text()",
            ],
            multiplicity="*",
        ),
        #WRONG-- this is the resource point of contact!!! should be gmd:MD_Metadata/gmd:contact
        ISOResponsibleParty(
            name="metadata-point-of-contact",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty",
            ],
            multiplicity="1..*",
        ),
        #metadata date stamp
        ISOElement(
            name="metadata-date",
            search_paths=[
                "gmd:dateStamp/gco:DateTime/text()",
                "gmd:dateStamp/gco:Date/text()",
            ],
            multiplicity="1",
        ),
        #spatial reference system for dataset, returns an identifier string; loses authority, 
        #  codeSpace and version if present
        ISOElement(
            name="spatial-reference-system",
            search_paths=[
                "gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        #resource title
        ISOElement(
            name="title",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()",
            ],
            multiplicity="1",
        ),
        #resource alternate title
        ISOElement(
            name="alternate-title",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:alternateTitle/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        #recource citation date; gets gmd:CI_Date object 
        ISOReferenceDate(
            name="dataset-reference-date",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date",
            ],
            multiplicity="1..*",
        ),
        #identifer string from resource citation 
        ISOElement(
            name="unique-resource-identifier",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
                "gmd:identificationInfo/gmd:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        #presentation form code or text string
        ISOElement(
            name="presentation-form",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:presentationForm/gmd:CI_PresentationFormCode/text()",
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:presentationForm/gmd:CI_PresentationFormCode/@codeListValue",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:presentationForm/gmd:CI_PresentationFormCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:presentationForm/gmd:CI_PresentationFormCode/@codeListValue",

            ],
            multiplicity="*",
        ),
        #abstract--description of resource
        ISOElement(
            name="abstract",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:abstract/gco:CharacterString/text()",
            ],
            multiplicity="1",
        ),
        #resource purpose
        ISOElement(
            name="purpose",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:purpose/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:purpose/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        #resource point of contact (returns whole CI_ResponsibleParty element); 
        #   ERROR!, remove gmd:/contact path
        ISOResponsibleParty(
            name="responsible-organisation",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty",
                "gmd:contact/gmd:CI_ResponsibleParty",
            ],
            multiplicity="1..*",
        ),
        #resource maintenance update frequency
        ISOElement(
            name="frequency-of-update",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/@codeListValue",
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode/text()",
            ],
            multiplicity="0..1",
        ),
        #resource maintenance notes
        ISOElement(
            name="maintenance-note",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceNote/gco:CharacterString/text()",
                "gmd:identificationInfo/gmd:SV_ServiceIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceNote/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        # ISO progress code-- status of the resource in development, review, publication, deprecated, 
        #   superseded or other workflow
        ISOElement(
            name="progress",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:status/gmd:MD_ProgressCode/@codeListValue",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:status/gmd:MD_ProgressCode/@codeListValue",
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:status/gmd:MD_ProgressCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:status/gmd:MD_ProgressCode/text()",
            ],
            multiplicity="*",
        ),
        #keywords; returns gmd:MD_Keywords object
        ISOKeyword(
            name="keywords",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords",
            ],
            multiplicity="*"
        ),
        #keywork text strings, stripped from MD_Keywords elements; 
        #  guess this returns an array of keywords that is inspected to see if any INSPIRE keywords are present?
        ISOElement(
            name="keyword-inspire-theme",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        # Deprecated: kept for backwards compatibilty.  This only gets keyword strings from serviceIdentification
        ISOElement(
            name="keyword-controlled-other",
            search_paths=[
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:keywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        # returns gmd:MD_Usage objects
        ISOUsage(
            name="usage",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceSpecificUsage/gmd:MD_Usage",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceSpecificUsage/gmd:MD_Usage",
            ],
            multiplicity="*"
        ),
        
        # ********************** CONSTRAINTS HANDLING *********************************
        # security constraints (MD_SecurityConstraints) are not captured.
        # legal constraints, gmd:otherConstraints text. Loses any useLimitation statement in MD_LegalConstraints.
        ISOElement(
            name="limitations-on-public-access",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        # MD_LegalConstraints access constraints code value or text
        # NOTE MD_LegalConstraints useConstraints code values are not captured.
        ISOElement(
            name="access-constraints",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode/@codeListValue",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode/@codeListValue",
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode/text()",
            ],
            multiplicity="*",
        ),
        # MD_Constraints useLimitation text.
        ISOElement(
            name="use-constraints",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_Constraints/gmd:useLimitation/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:resourceConstraints/gmd:MD_Constraints/gmd:useLimitation/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        # MD_AggregationInformation ojects
        ISOAggregationInfo(
            name="aggregation-info",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:aggregationInfo/gmd:MD_AggregateInformation",
                "gmd:identificationInfo/gmd:SV_ServiceIdentification/gmd:aggregationInfo/gmd:MD_AggregateInformation",
            ],
            multiplicity="*"
        ),
        # service type text
        ISOElement(
            name="spatial-data-service-type",
            search_paths=[
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:serviceType/gco:LocalName/text()",
            ],
            multiplicity="0..1",
        ),
        # spatial resolution Distance
        ISOElement(
            name="spatial-resolution",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/text()",
            ],
            multiplicity="0..1",
        ),
        # spatial resolution Distance unit of measure
        ISOElement(
            name="spatial-resolution-units",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/@uom",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance/@uom",
            ],
            multiplicity="0..1",
        ),
        # Spatial resolution equivalent scale denominator integer
        ISOElement(
            name="equivalent-scale",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer/text()",
            ],
            multiplicity="*",
        ),
        # Language of resource content
        ISOElement(
            name="dataset-language",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gmd:LanguageCode/@codeListValue",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:language/gmd:LanguageCode/@codeListValue",
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gmd:LanguageCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:language/gmd:LanguageCode/text()",
            ],
            multiplicity="*",
        ),
        #  ISO topic category code and text
        ISOElement(
            name="topic-category",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode/text()",
            ],
            multiplicity="*",
        ),
        # extent controlled, EMPTY SEARCH PATH
        ISOElement(
            name="extent-controlled",
            search_paths=[
            ],
            multiplicity="*",
        ),
        # Extent, geographic identifier text.  SUGGEST-- put in keywords with type=place
        ISOElement(
            name="extent-free-text",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicDescription/gmd:geographicIdentifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
            ],
            multiplicity="*",
        ),
        # geographic bounding box, EX_GeographicBoundingBox object
        ISOBoundingBox(
            name="bbox",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox",
            ],
            multiplicity="*",
        ),
        # temporal extent begin
        ISOElement(
            name="temporal-extent-begin",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text()",
            ],
            multiplicity="*",
        ),
        # temporal extent end
        ISOElement(
            name="temporal-extent-end",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition/text()",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition/text()",
            ],
            multiplicity="*",
        ),
        # vertical extent, EX_VerticalExtent objects
        ISOElement(
            name="vertical-extent",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:verticalElement/gmd:EX_VerticalExtent",
            ],
            multiplicity="*",
        ),
        # Service operates on link; path is property, The associated class populates teh elements object
        #   with xlink attributes only.  Assumes value is by reference only.
        ISOCoupledResources(
            name="coupled-resource",
            search_paths=[
                "gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn",
            ],
            multiplicity="*",
        ),
        # dataIdentification supplemental information string
        ISOElement(
            name="additional-information-source",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:supplementalInformation/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        # resource format. NOTE there are three possible paths (two added here by SMR 2014-08-28)
        ISODataFormat(
            name="data-format",
            search_paths=[
                "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format",
                "gmd:resourceFormat/gmd:MD_Format",
                "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorFormat/gmd:MD_Format",
            ],
            multiplicity="*",
        ),
        # distributor contact for resource
        ISOResponsibleParty(
            name="distributor",
            search_paths=[
                "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorContact/gmd:CI_ResponsibleParty",
            ],
            multiplicity="*",
        ),
        # CI_OnlineResource objects for Digital Transfer Options in distribution
        ISOResourceLocator(
            name="resource-locator",
            search_paths=[
                "gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource",
                "gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource"
            ],
            multiplicity="*",
        ),
        # PROBLEM!  Too broad, this will pull links that are in pointOfContact, userContactInfo,
        #  MD_MaintenanceInformation/contact, AND responsible party for citations in 
        #  aggregateDataSetName, thesaurusName, MD_Identification, possibly other places as well. 
        ISOResourceLocator(
            name="resource-locator-identification",
            search_paths=[
                "gmd:identificationInfo//gmd:CI_OnlineResource",
            ],
            multiplicity="*",
        ),
        # QUESTION:  this only gets conformance result for DomainConsistency, is that the intention?
        ISOElement(
            name="conformity-specification",
            search_paths=[
                "gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:specification",
            ],
            multiplicity="0..1",
        ),
        # conformance result (pass/fail only) for DQ_DomainConsistency report only
        ISOElement(
            name="conformity-pass",
            search_paths=[
                "gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:pass/gco:Boolean/text()",
            ],
            multiplicity="0..1",
        ),
        # conformance result explanation for DomainConsistency report.
        ISOElement(
            name="conformity-explanation",
            search_paths=[
                "gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_DomainConsistency/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        # lineage statement
        ISOElement(
            name="lineage",
            search_paths=[
                "gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString/text()",
            ],
            multiplicity="0..1",
        ),
        # browse graphic
        ISOBrowseGraphic(
            name="browse-graphic",
            search_paths=[
                "gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic",
                "gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic",
            ],
            multiplicity="*",
        ),

    ]

    def infer_values(self, values):
        # Todo: Infer name.
        self.infer_date_released(values)
        self.infer_date_updated(values)
        self.infer_date_created(values)
        self.infer_url(values)
        # Todo: Infer resources.
        self.infer_tags(values)
        self.infer_publisher(values)
        self.infer_contact(values)
        self.infer_contact_email(values)
        return values

    def infer_date_released(self, values):
        value = ''
        for date in values['dataset-reference-date']:
            if date['type'] == 'publication':
                value = date['value']
                break
        values['date-released'] = value

    def infer_date_updated(self, values):
        value = ''
        dates = []
        # Use last of several multiple revision dates.
        for date in values['dataset-reference-date']:
            if date['type'] == 'revision':
                dates.append(date['value'])

        if len(dates):
            if len(dates) > 1:
                dates.sort(reverse=True)
            value = dates[0]

        values['date-updated'] = value

    def infer_date_created(self, values):
        value = ''
        for date in values['dataset-reference-date']:
            if date['type'] == 'creation':
                value = date['value']
                break
        values['date-created'] = value

    def infer_url(self, values):
        value = ''
        for locator in values['resource-locator']:
            if locator['function'] == 'information':
                value = locator['url']
                break
        values['url'] = value

    def infer_tags(self, values):
        tags = []
        for key in ['keyword-inspire-theme', 'keyword-controlled-other']:
            for item in values[key]:
                if item not in tags:
                    tags.append(item)
        values['tags'] = tags

    def infer_publisher(self, values):
        value = ''
        for responsible_party in values['responsible-organisation']:
            if responsible_party['role'] == 'publisher':
                value = responsible_party['organisation-name']
            if value:
                break
        values['publisher'] = value

    def infer_contact(self, values):
        value = ''
        for responsible_party in values['responsible-organisation']:
            value = responsible_party['organisation-name']
            if value:
                break
        values['contact'] = value

    def infer_contact_email(self, values):
        value = ''
        for responsible_party in values['responsible-organisation']:
            if isinstance(responsible_party, dict) and \
               isinstance(responsible_party.get('contact-info'), dict) and \
               responsible_party['contact-info'].has_key('email'):
                value = responsible_party['contact-info']['email']
                if value:
                    break
        values['contact-email'] = value


class GeminiDocument(ISODocument):
    '''
    For backwards compatibility
    '''