from helper import FileHelper
import json
from trp import Document
from og import OutputGenerator

def processDocument(doc):
    for page in doc.pages:
        print("PAGE\n====================")
        for line in page.lines:
            print(f"Line: {line.text}--{line.confidence}")
            for word in line.words:
                print(f"Word: {word.text}--{word.confidence}")
        for table in page.tables:
            print("TABLE\n====================")
            for r, row in enumerate(table.rows):
                for c, cell in enumerate(row.cells):
                    print(f"Table[{r}][{c}] = {cell.text}-{cell.confidence}")
        print("Form (key/values)\n====================")
        for field in page.form.fields:
            k = ""
            v = ""
            if(field.key):
                k = field.key.text
            if(field.value):
                v = field.value.text
            print(f"Field: Key: {k}, Value: {v}")

        #Get field by key
        key = "Phone Number:"
        print(f"\nGet field by key ({key}):\n====================")
        if f := page.form.getFieldByKey(key):
            print(f"Field: Key: {f.key.text}, Value: {f.value.text}")

        #Search field by key
        key = "address"
        print(f"\nSearch field by key ({key}):\n====================")
        fields = page.form.searchFieldsByKey(key)
        for field in fields:
            print(f"Field: Key: {field.key}, Value: {field.value}")

def generateOutput(filePath, response):
    print("Generating output...")
    name, ext = FileHelper.getFileNameAndExtension(filePath)
    opg = OutputGenerator(response, f"{name}-v2-{ext}", True, True)
    opg.run()
    opg.generateInsights(True, True, 'es', 'us-east-1')

def run():
    filePath = "temp-response.json"
    response = json.loads(FileHelper.readFile(filePath))

    doc = Document(response)

    #print(doc)
    processDocument(doc)
    #generateOutput(filePath, response)

run()

