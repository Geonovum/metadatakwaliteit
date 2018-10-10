<html>
<head><title>Start pagina Metadata kwaliteit monitoring</title>
</head>
<body>
<h1>Start pagina Metadata kwaliteit monitoring</h1>
<p>
Dit is een tijdelijke pagina om de metadata kwaliteit monitoring te kunnen draaien.
</p>

<form action="execute.php" method="get">
<p>Kies de CSW:
<select name="csw">
    <option value="ngr" selected="selected">Heel NGR</option>
    <option value="inspire">INSPIRE CSW (Discovery Service)</option>
</select>
<p>
Voor het uitvoeren van de test, voer hieronder het formulier in (en wees daarna geduldig :)):
</p>
<p>
Wachtwoord: <input type="password" size="20" name="secret"/> &nbsp; <input type="submit" value="Monitoring starten"/>
</p>
<?php
$error=$_GET["error"];
if ($error) {
    echo "<h2>".$error."</h2>";
}
?>
</form>
<h2>Resultaten downloaden</h2>
<a href=".">Downloaden CSV bestanden</a>

<h2>E-mail adressen</h2>
<a href="processemail.php">Scores e-mailadressen verwerken</a>
</body>
