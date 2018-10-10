<?php
$secret=$_GET["secret"];
$csw = $_GET["csw"];
$password = "MYPASSWORD";
if ($secret==$password ){
    // echo "Start draaien, heb geduld en keer terug naar de vorige pagina";
    if ($csw=="inspire") {
        $output = shell_exec('/apps/metadatakwaliteit/git/metadatakwaliteit/src/python/run_inspire.sh');
    }
    else {
        $output = shell_exec('/apps/metadatakwaliteit/git/metadatakwaliteit/src/python/run.sh');
    }
    // echo "<pre>$output</pre>";
    header( 'Location: /metadatakwaliteit/' ) ; // TODO: set correct location for www
} else {
    header( 'Location: start.php?error=Wachtwoord ongeldig' ) ;
}
?>
