<?xml version="1.0" encoding="UTF-8"?>
<!-- 
Copyright (c) 2010, 2011, Geonovum, The Netherlands
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Geonovum nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL GEONOVUM BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:dc ="http://purl.org/dc/elements/1.1/" 
    xmlns:gmd="http://www.isotc211.org/2005/gmd" 
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:srv="http://www.isotc211.org/2005/srv" 	
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:xlink="http://www.w3.org/1999/xlink"><xsl:import href="common.xsl"/><xsl:output method="text" media-type="application/vnd.ms-excel" version="1.0" encoding="utf-8" indent="no"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="/" xml:space="default">fileIdentifier<xsl:call-template name="sep"/>type metadata<xsl:call-template name="sep"/>metadata organisatie<xsl:call-template name="sep"/>metadata email<xsl:call-template name="sep"/>rol organisatie metadata<xsl:call-template name="sep"/>metadata datum<xsl:call-template name="sep"/>titel metadata<xsl:call-template name="sep"/>datum type van de bron<xsl:call-template name="sep"/>unieke identifier van de bron<xsl:call-template name="sep"/>specificatie titel<xsl:call-template name="sep"/>specificatie datum<xsl:call-template name="sep"/>specificatie datum type<xsl:call-template name="sep"/>conformiteit<xsl:call-template name="sep"/>trefwoorden<xsl:call-template name="sep"/>trefwoorden2<xsl:call-template name="sep"/>thesaurusnaam<xsl:call-template name="sep"/>datum thesaurus<xsl:call-template name="sep"/>datum type thesaurus<xsl:call-template name="sep"/>coupled resource metadata URL<xsl:call-template name="sep"/>coupled resource UUID<xsl:call-template name="sep"/>service type<xsl:call-template name="sep"/>service type version<xsl:call-template name="sep"/>eerste connect point linkage<xsl:call-template name="sep"/>online resource<xsl:call-template name="sep"/>protocol<xsl:call-template name="sep"/>gebruiksbeperkingen<xsl:call-template name="sep"/>Juridische toegangsrestricties<xsl:call-template name="sep"/>Juridische gebruiksrestricties<xsl:call-template name="sep"/>Overige beperkingen<xsl:call-template name="sep"/>Veiligheidsbeperkingen<xsl:call-template name="sep"/>Toelichting<xsl:call-template name="newLine"/><xsl:apply-templates/>
    </xsl:template> 
    <xsl:template match="gmd:MD_Metadata">
        <xsl:if test="gmd:hierarchyLevel[1]/gmd:MD_ScopeCode/@codeListValue='service'">
            <xsl:value-of select="gmd:fileIdentifier/gco:CharacterString"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:hierarchyLevel[1]/gmd:MD_ScopeCode/@codeListValue"/><xsl:call-template name="sep"/>        
            <xsl:call-template name="escape"><xsl:with-param name="string" select="gmd:contact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:contact/gmd:CI_ResponsibleParty/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:contact/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode/@codeListValue"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:dateStamp/gco:Date"/><xsl:call-template name="sep"/>
            <xsl:call-template name="escape"><xsl:with-param name="string" select="gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeListValue"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:identificationInfo/*/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString"/><xsl:call-template name="sep"/>
            <xsl:call-template name="escape"><xsl:with-param name="string" select="gmd:dataQualityInfo/*/gmd:report/*/gmd:result/*/gmd:specification/gmd:CI_Citation/gmd:title/gco:CharacterString"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:dataQualityInfo/*/gmd:report/*/gmd:result/*/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:dataQualityInfo/*/gmd:report/*/gmd:result/*/gmd:specification/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeListValue"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:dataQualityInfo/*/gmd:report/*/gmd:result/*/gmd:pass/gco:Boolean"/><xsl:call-template name="sep"/>
            <xsl:call-template name="keywords"><xsl:with-param name="keywordNode" select="gmd:identificationInfo/*/gmd:descriptiveKeywords/gmd:MD_Keywords"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="keywords2"><xsl:with-param name="keywordNode" select="gmd:identificationInfo/*/gmd:descriptiveKeywords/gmd:MD_Keywords"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="escape"><xsl:with-param name="string" select="gmd:identificationInfo/*/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:identificationInfo/*/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:thesaurusName/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date"/><xsl:call-template name="sep"/>        
            <xsl:value-of select="gmd:identificationInfo/*/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:thesaurusName/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeListValue"/><xsl:call-template name="sep"/>
            <xsl:call-template name="coupledresourceidentifier"><xsl:with-param name="serviceIdentificationNode" select="gmd:identificationInfo/srv:SV_ServiceIdentification"/></xsl:call-template><xsl:call-template name="sep"/>        
            <xsl:call-template name="coupledresourcemetadata"><xsl:with-param name="serviceIdentificationNode" select="gmd:identificationInfo/srv:SV_ServiceIdentification"/></xsl:call-template><xsl:call-template name="sep"/>               
            <xsl:value-of select="gmd:identificationInfo/*/srv:serviceType/gco:LocalName"/><xsl:call-template name="sep"/> 
            <xsl:value-of select="gmd:identificationInfo/*/srv:serviceTypeVersion/gco:CharacterString"/><xsl:call-template name="sep"/>
            <xsl:call-template name="connectpointlinkage"><xsl:with-param name="containsOperationsNode" select="gmd:identificationInfo/*/srv:containsOperations"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:distributionInfo/*/gmd:transferOptions[1]/*/gmd:onLine/*/gmd:linkage/gmd:URL"/><xsl:call-template name="sep"/>
            <xsl:value-of select="gmd:distributionInfo/*/gmd:transferOptions[1]/*/gmd:onLine/*/gmd:linkage/gmd:protocol"/><xsl:call-template name="sep"/>
            <xsl:call-template name="gebruiksbeperkingen"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="juridischetoegangsrestricties"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="juridischegebruiksrestricties"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="overigebeperkingen"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template><xsl:call-template name="sep"/>
            <xsl:call-template name="veiligheidsbeperkingen"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template><xsl:call-template name="sep"/>
		    <xsl:call-template name="toelichting"><xsl:with-param name="identificationNode" select="gmd:identificationInfo[1]/*"/></xsl:call-template>            
			<xsl:call-template name="newLine"/>
        </xsl:if>
</xsl:template>
</xsl:stylesheet>
