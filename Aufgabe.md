Ich möchte über IB Trader Workstation oder frei im Internet verfügbare Quellen die wichtigsten Wirtschaftsparameter für den Euroraum als auch den Dollarraum abrufen. 
Ich dachte da an Ölpreis, Goldpreis, Inflation, Verbraucherpreise, Volatilität, Kuperpreis, große Indizies oder ETFs, Wechselkurse. 
Mache mir eine Tabelle mit den 30 wichtigsten Werten welche ich per Python abrufen kann. 
Gib den jeweiligen Ticker mit an.

Am Ende soll ein Tool erstellt werden, welches die Kauf und verkaufsempfehlungen für
DBK
SIE
ALV
DTE 
RGLD
AMZN
BNP

liefert.

* Der API Key für https://fred.stlouisfed.org/ liegt in fred_API_Key.txt
* Die Github Zugangsdaten liegen in Github_Token.txt
* Erstelle eine readme.txt in welcher das Programm beschrieben wird und die Installation und der Aufruf beschrieben wird
* Ergänze in der Readme die Bewertungsmaßstäbe für die Aktien, wie werden die Parameter gewichtet, was wird berücksichtigt. 

1) Speicher die Wirtsschaftsparameter als auch die Aktienkurse in einer lokalen SQL Datenbank. Lade die Kurse der letzten 20 Jahre herunter. Lade immer nur die Kurse nach, welche noch nicht in der Datenbank sind 
2) Finde Korellationen zwischen den Aktienkursen und den Wirtschaftsdaten. Welche Wirtschaftsdaten laufen den Aktienkursen vorraus und können als Indikator genutzt werden?

