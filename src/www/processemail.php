<?php
$secret=$_REQUEST["secret"];
$process = $_REQUEST["process"];
$password = "MYPASSWORD";
if ($process=="1" && $_REQUEST["openfilename"]){
    // echo "Start draaien, heb geduld en keer terug naar de vorige pagina";
    $openFileName = $_REQUEST["openfilename"];
    if ($secret==$password && $openFileName && $_REQUEST["csvdata"]) {
        $csvData = $_REQUEST["csvdata"];
        header( 'Content-Type: text/plain' );
        echo $csvData;
        $fh = fopen($openFileName, 'w') or die("can't open file");
        fwrite($fh, $csvData);
        fclose($fh);
        // now process emailadresses
        $output = shell_exec('sh /apps/metadatakwaliteit/git/metadatakwaliteit/src/python/processemails.sh '.$openFileName);
    } else {
        // wrong password or filename is missing
        http_response_code(401); // not authorized
        // break;
    }
    // $timestamp
    // echo "<pre>$output</pre>";
    // header( 'Location: /metadatakwaliteit/' ) ; // TODO: set correct location for www
} else {
    // lots of HTML and stuff
?>
<html>
    <head>
        <script type="text/javascript" src="jquery.js"></script>
        <style>
            #emailadressfiles{
                font-size: 0.9em;
            }
            /* geldig */
            .email1{
                background-color: #ddffdd;
            }
            /* ongeldig */
            .email0{
                background-color: #ffdddd;
            }
            #csv, .csvcontents {
                display: none;
            }
            #resultmessage {
                font-size: 1.2em;
                background-color: #ddffdd;
            }

        </style>
    </head>
    <body>
        <h1>Metadatakwaliteit email gegevens verwerken</h1>
        <?php
            // header( 'Location: start.php?error=Wachtwoord ongeldig' ) ;
            $fileNames = array();
            if ($handle = opendir('.')) {
                while (false !== ($entry = readdir($handle))) {
                    // TODO: order
                    if ($entry != "." && $entry != ".." && strpos($entry,"emailadressen.csv") > 1 ){
                        array_push($fileNames, $entry);
                    }
                }
                closedir($handle);
            }
            asort($fileNames);
            echo "<ul id='emailadressfiles'>";
            foreach ($fileNames as $entry) {
                echo "<li><button type='button' onclick='openEmails(\"$entry\")'>$entry</button></li>";
            }
            // while ()
            // echo "<li><button type='button' onclick='openEmails(\"$entry\")'>$entry</button></li>";

            echo "</ul>";
        ?>
        <div>
            <ol id="list">
            </ol>
            <label for="secret">Wachtwoord</label> <input type="password" value="" id="secret"/>
            <button type="button" onclick="saveResults()">Sla scores op en bereken totaalscores</button>
            <hr>
            <div id="resultmessage">
            </div>
            <a href=".">Downloaden CSV bestanden</a>
            <h3 class="csvcontents">Inhoud CSV-bestand:</h3>
            <textarea id="csv" cols="150" rows="50"></textarea>
        </div>
        <script>
            var csvData = "";
            var csvRows = new Array();
            var openFileName = "";
            function doStart() {
                // openFileName = "<?=$openFileName?>";
                // jQuery.get("<?=$openFileName?>", showData, "text");
            }
            function showData(data) {
                csvData = data;
                var listElem = jQuery("ol#list").html("");
                // first: if the name
                var list = data.split('"\r\n"');
                // var list = data.split('","');
                jQuery.each(list, function (i, item) {
                    var cells = item.split('","');
                    if (cells.length > 1) {
                        // cleanup
                        cells[0] = cells[0].replace('"', '');
                        cells[1] = cells[1].replace('"\r\n', '');
                        if (cells.length < 3) {
                            cells[2] = "0";
                        } else {
                            cells[2] = cells[2].replace('"\r\n', '');
                            cells[2] = cells[2].replace('"','')
                        }
                        var newVal = "1";
                        var strNewVal = "geldig";
                        var strCurrent = "ongeldig"
                        if (cells[2]!="0") {
                            newVal = "0";
                            strNewVal = "ongeldig";
                            strCurrent = "geldig"
                        }
                        jQuery("<li class='email"+cells[2]+"'>").html("<button type='button' onclick='setEmail("+i+", this.value)' value='"+newVal+"'>Zet score "+strNewVal+"</button> voor: "+ cells[1]+" (nu:"+strCurrent+"), van organisatie:" + cells[0]).appendTo(listElem);
                        csvRows[i] = cells;
                    }
                });
                jQuery('#csv').text(data);
                // console.log(csvData);
            }
            doStart();

            function openEmails(fileName){
                openFileName = fileName;
                jQuery.get(openFileName, showData, "text");
            }

            function setEmail(index, value) {
                csvRows[index][2] = value;
                csvData = serializeCsv(csvRows)
                showData(csvData);
            }
            function serializeCsv(rows) {
                var csvStr = "";
                var sep = '","';
                var endRow = '"\r\n';
                for (var i=0; i < rows.length; i++) {
                    if (i+1==rows.length) endRow = '"';
                    csvStr+='"' + rows[i][0] + sep + rows[i][1] + sep + rows[i][2] + endRow;
                }
                return csvStr;
            }
            function saveResults() {
                // current filename
                var params = {"openfilename" : openFileName, "csvdata" : csvData, "secret": jQuery("#secret").val() , "process":"1"}
                var success = function(data) {
                    // console.log(data);
                    // alert("Resultaat opgeslagen");
                    showData(data);
                    var datasetsFileName = openFileName.replace("emailadressen.csv","datasetswaardes_email.csv");
                    var servicesFileName = openFileName.replace("emailadressen.csv","serviceswaardes_email.csv");;
                    jQuery("#resultmessage").html("Scores emailadressen verwerkt. Bestanden te downloaden via: <ul><li><a target='_blank' href='"+datasetsFileName+"'>Datasets: "+datasetsFileName+"</a></li><li><a target='_blank' href='"+servicesFileName+"'>Services: "+servicesFileName+"</a></li></ul>");
                };

                var failure = function(data) {
                    // console.log(data);
                    alert("Fout opgetreden. Is het opgegeven wachtwoord wel juist?");
                    // showData(data);
                };
                jQuery.post('processemail.php', params, success).fail(failure);// jqeury shorthand signature does not allow direct assignment of failure function
            }

        </script>

    </body>
</html>
<?php
}
?>
