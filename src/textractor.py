import sys
import os
from urllib.parse import urlparse
import boto3
import time
from tdp import DocumentProcessor
from og import OutputGenerator
from helper import FileHelper, S3Helper

class Textractor:
    def getInputParameters(self, args):
        event = {}
        if args:
            i = 0
            while (i < len(args)):
                if (args[i] == '--documents'):
                    event['documents'] = args[i+1]
                    i += 1
                if (args[i] == '--region'):
                    event['region'] = args[i+1]
                    i += 1
                if(args[i] == '--text'):
                    event['text'] = True
                if(args[i] == '--forms'):
                    event['forms'] = True
                if(args[i] == '--tables'):
                    event['tables'] = True
                if(args[i] == '--insights'):
                    event['insights'] = True
                if(args[i] == '--medical-insights'):
                    event['medical-insights'] = True
                if (args[i] == '--translate'):
                    event['translate'] = args[i+1]
                    i += 1

                i += 1
        return event

    def validateInput(self, args):

        event = self.getInputParameters(args)

        if 'documents' not in event:
            raise Exception("Document or path to a foler or S3 bucket containing documents is required.")

        inputDocument = event['documents']
        idl = inputDocument.lower()

        bucketName = None
        documents = []
        awsRegion = 'us-east-1'

        if (idl.startswith("s3://")):
            o = urlparse(inputDocument)
            bucketName = o.netloc
            path = o.path[1:]
            if ar := S3Helper.getS3BucketRegion(bucketName):
                awsRegion = ar

            if(idl.endswith("/")):
                allowedFileTypes = ["jpg", "jpeg", "png", "pdf"]
                documents = S3Helper.getFileNames(awsRegion, bucketName, path, 1, allowedFileTypes)
            else:
                documents.append(path)
        else:
            if(idl.endswith("/")):
                allowedFileTypes = ["jpg", "jpeg", "png"]
                documents = FileHelper.getFileNames(inputDocument, allowedFileTypes)
            else:
                documents.append(inputDocument)

            if('region' in event):
                awsRegion = event['region']

        return {
            "bucketName": bucketName,
            "documents": documents,
            "awsRegion": awsRegion,
            "text": 'text' in event,
            "forms": 'forms' in event,
            "tables": 'tables' in event,
            "insights": 'insights' in event,
            "medical-insights": 'medical-insights' in event,
            "translate": event["translate"] if ("translate" in event) else "",
        }

    def processDocument(self, ips, i, document):
        print(f"\nTextracting Document # {i}: {document}")
        print('=' * (len(document)+30))

        # Get document textracted
        dp = DocumentProcessor(ips["bucketName"], document, ips["awsRegion"], ips["text"], ips["forms"], ips["tables"])
        response = dp.run()
        print("Recieved Textract response...")

        #FileHelper.writeToFile("temp-response.json", json.dumps(response))

        #Generate output files
        print("Generating output...")
        name, ext = FileHelper.getFileNameAndExtension(document)
        opg = OutputGenerator(response, f"{name}-{ext}", ips["forms"], ips["tables"])
        opg.run()

        if(ips["insights"] or ips["medical-insights"] or ips["translate"]):
            opg.generateInsights(ips["insights"], ips["medical-insights"], ips["translate"], ips["awsRegion"])

        print(f"{document} textracted successfully.")

    def printFormatException(self, e):
        print(f"Invalid input: {e}")
        print("Valid format:")
        print('- python3 textractor.py --documents mydoc.jpg --text --forms --tables --region us-east-1')
        print('- python3 textractor.py --documents ./myfolder/ --text --forms --tables')
        print('- python3 textractor.py --document s3://mybucket/mydoc.pdf --text --forms --tables')
        print('- python3 textractor.py --document s3://mybucket/ --text --forms --tables')

    def run(self):

        ips = None
        try:
            ips = self.validateInput(sys.argv)
        except Exception as e:
            self.printFormatException(e)

        #try:
        i = 1
        totalDocuments = len(ips["documents"])

        print("\n")
        print('*' * 60)
        print(f"Total input documents: {totalDocuments}")
        print('*' * 60)

        for document in ips["documents"]:
            self.processDocument(ips, i, document)

            remaining = len(ips["documents"])-i

            if (remaining > 0):
                print(f"\nRemaining documents: {remaining}")

                print("\nTaking a short break...")
                time.sleep(20)
                print("Allright, ready to go...\n")

            i = i + 1

        print("\n")
        print('*' * 60)
        print(f"Successfully textracted documents: {totalDocuments}")
        print('*' * 60)
        print("\n")
        #except Exception as e:
        #    print("Something went wrong:\n====================================================\n{}".format(e))

Textractor().run()
