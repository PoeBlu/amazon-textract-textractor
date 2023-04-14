import boto3
from helper import AwsHelper

class TextTranslater:
    def __init__(self, source, target, awsRegion):
        ''' Constructor. '''
        self.source = source
        self.target = target
        self.awsRegion = awsRegion

        self.client = AwsHelper().getClient('translate', self.awsRegion)

    def getTranslation(self, text):

        response = self.client.translate_text(
            Text=text,
            SourceLanguageCode=self.source,
            TargetLanguageCode=self.target
        )
        return response['TranslatedText']

class TextMedicalAnalyzer:
    def __init__(self, awsRegion):
        ''' Constructor. '''
        self.awsRegion = awsRegion
        self.client = AwsHelper().getClient('comprehendmedical', self.awsRegion)

    def getMedicalEntities(self, text):
        return self.client.detect_entities(
            Text=text,
        )

    def getPhi(self, text):
        response = self.client.detect_phi(
            Text=text,
        )
        return response['Entities']

class TextAnalyzer:
    def __init__(self, languageCode, awsRegion):
        ''' Constructor. '''
        self.languageCode = languageCode
        self.awsRegion = awsRegion
        self.client = AwsHelper().getClient('comprehend', self.awsRegion)

    def getSentiment(self, text):
        return self.client.detect_sentiment(
            Text=text, LanguageCode=self.languageCode
        )

    def getSyntax(self, text):
        return self.client.detect_syntax(Text=text, LanguageCode=self.languageCode)

    def getEntities(self, text):
        return self.client.detect_entities(
            Text=text, LanguageCode=self.languageCode
        )

    def getKeyPhrases(self, text):
        return self.client.detect_key_phrases(
            Text=text, LanguageCode=self.languageCode
        )
