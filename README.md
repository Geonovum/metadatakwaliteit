# Metadata kwaliteits monitor (MKM)
**Nota bene: De metadata kwaliteits monitor (MKM) is ontwikkeld voor intern gebruik bij Geonovum. De code is enkele jaren oud en bevat specifieke zaken voor de Geonovum server. Wees voorzichtig bij gebruik door derden. Geonovum biedt nadrukkelijk geen ondersteuning aan op de tool bij gebruik door derden.**

De metadata kwaliteits monitor (MKM) maakt automatisch rapportages over de kwaliteit van metadata uit een Catalogue Servcie for the Web (CSW).

De kwaliteitseisen zijn geformuleerd door Geonovum. De controles op die eisen bestaan uit zaken als:
* aanwezigheid van elementen
* is een element nuttig ingevuld, bijvoorbeeld is de samenvatting van een minimale lengte?
* controle of URLs geldig zijn en werken

De MKM voert de controles uit en bepaalt scores per controle. Deze scores worden gewogen en resulteren in een rapportage per metadata record.

De rapportages zijn online in te zien en te downloaden. De rapportages dienen handmatig, als spreadsheets, aangepast te kunnen worden.

## Resultaten
De MKM maakt gebruik van CSV om (tussen)resultaten op te slaan en te verwerken. Dit maakt het mogelijk om de resultaten in spreadsheet programma's verder te analyseren, indien gewenst.

## Uitvoeren

De MKM maakt gebruik van Python om de metadata te analyseren en voor het doorrekenen van de spreadsheets.

Vanwege de controle op werking van emailadressen is het nodig dat de rapportages apart gegenereerd kunnen worden en later opnieuw doorgerekend.

Er zijn enkele zeer basale PHP scripts en Linux shell scripts om de MKM tool te starten en om achteraf de scores voor emailadressen in te voeren.

## Configuratie
In de directory config staan enkele bestanden voor conifguratie: codelijsten (in CSV formaat), de scores en gewichten voor de resultaten en de configuratie van de tool zelf. Deze laastte bevat bijvoorbeeld de locaties voor bestandsopslag en verwijzingen naar de codelijsten.

## Waarom geen ...?
ETF: gaat uit van true/false validatie. Dit vraagt om wat omslachtigere aanpak bij bepalen van scores. Daarnaast dient er voor de webGUI nog aanvullende technologie ingezet te worden, omdat het ETF een standalone tool is van zichzelf. (zie ook doc/afwegingen.txt)
...

## Aanpak op hoofdlijnen
1. CSW bevragen, per 5 (te configureren) records om een lijst van identifiers op te bouwen
2. per record: checks uitvoeren en in CSVs wegschrijven
3. scores bijhouden per check
4. weging toepassen op scores
5. de emailscores handmatig achteraf verwerken

Er zijn drie cycli: 1 voor opvragen dataset metadata, 1 voor dataset series, 1 voor service metadata.

## emailscores verwerken
Bijvoorbeeld om de resultaten van emailadressen op te nemen. Via de WebGUI moet het daarom mogelijk zijn (aangepaste) spreadsheets te uploaden en opnieuw door te rekenen met een wegingslijst.

## Dependencies
Python versie 2.7.3

libxml2, libxml2-devel
libxslt, libxslt-devel
python-devel

Python: setuptools, lxml, OWSLib
**NOTE:** OWSLib needsto be patched manually to work properly for the MKM tool.

## Installation (English)

Need to fix iso.py in OWSLib, to get contact etc working. Fixes are in repo: ```src/python/patches/owslib/```.

Do this by fixing the file iso.py (find it in your oython installation)  and then recompile the class, using:
$ python
>>> import py_compile
>>> py_compile.compile("iso.py")

Similar must be done for csw.py and util.py.
Patches are available in this repo.

## License
BSD License, see LICENSE.txt
