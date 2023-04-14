import json
from helper import FileHelper
from ta import TextAnalyzer, TextMedicalAnalyzer, TextTranslater
from trp import *

class OutputGenerator:
    def __init__(self, response, fileName, forms, tables):
        self.response = response
        self.fileName = fileName
        self.forms = forms
        self.tables = tables

        self.document = Document(self.response)

    def _outputWords(self, page, p):
        csvData = []
        for line in page.lines:
            for word in line.words:
                csvItem = [word.id]
                if(word.text):
                    csvItem.append(word.text)
                else:
                    csvItem.append("")
                csvData.append(csvItem)
        csvFieldNames = ['Word-Id', 'Word-Text']
        FileHelper.writeCSV(
            f"{self.fileName}-page-{p}-words.csv", csvFieldNames, csvData
        )

    def _outputText(self, page, p):
        text = page.text
        FileHelper.writeToFile(f"{self.fileName}-page-{p}-text.txt", text)

        textInReadingOrder = page.getTextInReadingOrder()
        FileHelper.writeToFile(
            f"{self.fileName}-page-{p}-text-inreadingorder.txt", textInReadingOrder
        )

    def _outputForm(self, page, p):
        csvData = []
        for field in page.form.fields:
            csvItem  = []
            if field.key:
                csvItem.extend((field.key.text, field.key.confidence))
            else:
                csvItem.extend(("", ""))
            if field.value:
                csvItem.extend((field.value.text, field.value.confidence))
            else:
                csvItem.extend(("", ""))
            csvData.append(csvItem)
        csvFieldNames = ['Key', 'KeyConfidence', 'Value', 'ValueConfidence']
        FileHelper.writeCSV(
            f"{self.fileName}-page-{p}-forms.csv", csvFieldNames, csvData
        )

    def _outputTable(self, page, p):

        csvData = []
        for table in page.tables:
            csvRow = ["Table"]
            csvData.append(csvRow)
            for row in table.rows:
                csvRow = [cell.text for cell in row.cells]
                csvData.append(csvRow)
            csvData.extend(([], []))
        FileHelper.writeCSVRaw(f"{self.fileName}-page-{p}-tables.csv", csvData)

    def run(self):

        if(not self.document.pages):
            return

        FileHelper.writeToFile(
            f"{self.fileName}-response.json", json.dumps(self.response)
        )

        print(f"Total Pages in Document: {len(self.document.pages)}")

        p = 1
        for page in self.document.pages:

            FileHelper.writeToFile(
                f"{self.fileName}-page-{p}-response.json", json.dumps(page.blocks)
            )

            self._outputWords(page, p)

            self._outputText(page, p)

            if(self.forms):
                self._outputForm(page, p)

            if(self.tables):
                self._outputTable(page, p)

            p = p + 1

    def _insights(self, start, subText, sentiment, syntax, entities, keyPhrases, ta):
        # Sentiment
        dsentiment = ta.getSentiment(subText)
        dsentimentRow = [dsentiment["Sentiment"]]
        sentiment.append(dsentimentRow)

        # Syntax
        dsyntax = ta.getSyntax(subText)
        for dst in dsyntax['SyntaxTokens']:
            dsyntaxRow = [
                dst["PartOfSpeech"]["Tag"],
                dst["PartOfSpeech"]["Score"],
                dst["Text"],
                int(dst["BeginOffset"]) + start,
                int(dst["EndOffset"]) + start,
            ]
            syntax.append(dsyntaxRow)

        # Entities
        dentities = ta.getEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = [
                dent["Type"],
                dent["Text"],
                dent["Score"],
                int(dent["BeginOffset"]) + start,
                int(dent["EndOffset"]) + start,
            ]
            entities.append(dentitiesRow)

        # Key Phrases
        dkeyPhrases = ta.getKeyPhrases(subText)
        for dkphrase in dkeyPhrases['KeyPhrases']:
            dkeyPhrasesRow = [
                dkphrase["Text"],
                dkphrase["Score"],
                int(dkphrase["BeginOffset"]) + start,
                int(dkphrase["EndOffset"]) + start,
            ]
            keyPhrases.append(dkeyPhrasesRow)

    def _medicalInsights(self, start, subText, medicalEntities, phi, tma):
        # Entities
        dentities = tma.getMedicalEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = [
                dent["Text"],
                dent["Type"],
                dent["Category"],
                dent["Score"],
                int(dent["BeginOffset"]) + start,
                int(dent["EndOffset"]) + start,
            ]
            medicalEntities.append(dentitiesRow)


        phi.extend(tma.getPhi(subText))

    def _generateInsightsPerDocument(self, page, p, insights, medicalInsights, translate, ta, tma, tt):

        maxLen = 2000

        text = page.text

        start = 0
        sl = len(text)

        sentiment = []
        syntax = []
        entities = []
        keyPhrases = []
        medicalEntities = []
        phi = []
        translation = ""

        while (start < sl):
            end = start + maxLen
            end = min(end, sl)
            subText = text[start:end]

            if(insights):
                self._insights(start, text, sentiment, syntax, entities, keyPhrases, ta)

            if(medicalInsights):
                self._medicalInsights(start, text, medicalEntities, phi, tma)

            if(translate):
                translation = translation + tt.getTranslation(subText) + "\n"

            start = end

        if insights:
            FileHelper.writeCSV(
                f"{self.fileName}-page-{p}-insights-sentiment.csv",
                ["Sentiment"],
                sentiment,
            )
            FileHelper.writeCSV(
                f"{self.fileName}-page-{p}-insights-entities.csv",
                ["Type", "Text", "Score", "BeginOffset", "EndOffset"],
                entities,
            )
            FileHelper.writeCSV(
                f"{self.fileName}-page-{p}-insights-syntax.csv",
                [
                    "PartOfSpeech-Tag",
                    "PartOfSpeech-Score",
                    "Text",
                    "BeginOffset",
                    "EndOffset",
                ],
                syntax,
            )
            FileHelper.writeCSV(
                f"{self.fileName}-page-{p}-insights-keyPhrases.csv",
                ["Text", "Score", "BeginOffset", "EndOffset"],
                keyPhrases,
            )

        if medicalInsights:
            FileHelper.writeCSV(
                f"{self.fileName}-page-{p}-medical-insights-entities.csv",
                ["Text", "Type", "Category", "Score", "BeginOffset", "EndOffset"],
                medicalEntities,
            )

            FileHelper.writeToFile(
                f"{self.fileName}-page-{p}-medical-insights-phi.json",
                json.dumps(phi),
            )

        if translate:
            FileHelper.writeToFile(
                f"{self.fileName}-page-{p}-text-translation.txt", translation
            )

    def generateInsights(self, insights, medicalInsights, translate, awsRegion):

        print("Generating insights...")

        if(not self.document.pages):
            return

        ta = TextAnalyzer('en', awsRegion)
        tma = TextMedicalAnalyzer(awsRegion)

        tt = TextTranslater('en', translate, awsRegion) if translate else None
        p = 1
        for page in self.document.pages:
            self._generateInsightsPerDocument(page, p, insights, medicalInsights, translate, ta, tma, tt)
            p = p + 1
