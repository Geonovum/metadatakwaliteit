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
    xmlns:xlink="http://www.w3.org/1999/xlink">
    <xsl:strip-space elements="*"/>

    <!-- linebreak = &#x10; -->    
    <xsl:template name="newLine"><xsl:text>&#10;</xsl:text></xsl:template>
    
    <!-- tab = &#x9; --> 
    <xsl:template name="sep"><xsl:text>&#x9;</xsl:text></xsl:template>

    <xsl:template name="keywords">
        <xsl:param name="keywordNode"></xsl:param>
        <xsl:for-each select="$keywordNode/gmd:keyword[1]"><xsl:value-of select="gco:CharacterString"/><xsl:if test="count($keywordNode/gmd:keyword)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>
	
	<xsl:template name="keywords2">
        <xsl:param name="keywordNode"></xsl:param>
        <xsl:for-each select="$keywordNode/gmd:keyword"><xsl:value-of select="gco:CharacterString"/><xsl:if test="count($keywordNode/gmd:keyword)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>

    <xsl:template name="onlineprotocol">
        <xsl:param name="onLineNode"></xsl:param>
        <xsl:for-each select="$onLineNode/gmd:CI_OnlineResource/gmd:protocol"><xsl:value-of select="gco:CharacterString"/><xsl:if test="count($onLineNode/gmd:CI_OnlineResource/gmd:protocol)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>

    <xsl:template name="onlineresources">
        <xsl:param name="onLineNode"></xsl:param>
        <xsl:for-each select="$onLineNode/gmd:CI_OnlineResource/gmd:linkage"><xsl:value-of select="gmd:URL"/><xsl:if test="count($onLineNode/gmd:CI_OnlineResource/gmd:linkage)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>

    <xsl:template name="gebruiksbeperkingen">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_Constraints/gmd:useLimitation"><xsl:call-template name="escape"><xsl:with-param name="string" select="gco:CharacterString"/></xsl:call-template> // </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="juridischetoegangsrestricties">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:accessConstraints/gmd:MD_RestrictionCode"><xsl:value-of select="@codeListValue"/> // </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="juridischegebruiksrestricties">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode"><xsl:value-of select="@codeListValue"/> // </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="overigebeperkingen">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:otherConstraints"><xsl:call-template name="escape"><xsl:with-param name="string" select="gco:CharacterString"/></xsl:call-template> // </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="veiligheidsbeperkingen">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_ClassificationCode"><xsl:value-of select="@codeListValue"/> // </xsl:for-each>
    </xsl:template>

    <xsl:template name="toelichting">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:classification/gmd:userNote"><xsl:call-template name="escape"><xsl:with-param name="string" select="gco:CharacterString"/></xsl:call-template> // </xsl:for-each>
    </xsl:template>

    <xsl:template name="temporeledekking">
        <xsl:param name="identificationNode"></xsl:param>
        <xsl:for-each select="$identificationNode/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/*/*"><xsl:value-of select="."/>, </xsl:for-each>
    </xsl:template>

	<xsl:template name="coupledresourcemetadata">
        <xsl:param name="serviceIdentificationNode"></xsl:param>
        <xsl:for-each select="$serviceIdentificationNode/srv:operatesOn"><xsl:value-of select="./@uuidref"/><xsl:if test="count($serviceIdentificationNode/srv:operatesOn)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>
	
    <xsl:template name="coupledresourceidentifier">
        <xsl:param name="serviceIdentificationNode"></xsl:param>
        <xsl:for-each select="$serviceIdentificationNode/srv:operatesOn"><xsl:value-of select="./@xlink:href"/><xsl:if test="count($serviceIdentificationNode/srv:operatesOn)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>

    <xsl:template name="connectpointlinkage">
        <xsl:param name="containsOperationsNode"></xsl:param>
        <!-- Thijs: agreed with Ine de Visser to show only the first connect point linkage. Otherwise, remove [1] after SV_OperationMetadata -->
        <xsl:for-each select="$containsOperationsNode/srv:SV_OperationMetadata[1]"><xsl:value-of select="srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage/gmd:URL"/><xsl:if test="count($containsOperationsNode/srv:SV_OperationMetadata)&gt;position()">, </xsl:if></xsl:for-each>
    </xsl:template>

    <!-- Escape tabs and new line characters-->
    <xsl:template name="escape">
        <xsl:param name="string"></xsl:param>
        <xsl:value-of select="translate(translate($string, '&#10;', ' ' ), '&#x9;', ' ' )"/>
    </xsl:template>
</xsl:stylesheet>
