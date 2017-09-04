import csv
import json
import ioHelpers as io

INPUT_DIR = 'D:/mnt/data/empyr'
OFFER_FILES = io.getFiles(searchDirectories = INPUT_DIR, fileExtensions = '*.json')

MERCHANTS = {}

for offerFile in OFFER_FILES:
    try:
        offerDetails = ''.join(open(file = offerFile, mode = 'tr', encoding = 'utf-8').readlines()).strip('\n')
        offersJSON = json.loads(offerDetails)
        for offer in offersJSON['results']:
            MERCHANTS[offer['id']] = {
                'name': '',
                'category': '',
                'source': offerFile
            }

            if 'name' in offer:
                MERCHANTS[offer['id']]['name'] = offer['name'].strip()

            if 'primaryCategory' in offer:
                MERCHANTS[offer['id']]['category'] = offer['primaryCategory'].strip()

    except BaseException as err:
        print(str(err))
        pass

with open(INPUT_DIR + '/offer_merchants.csv', 'w') as outputFile:
    columns = ['name', 'category', 'source']
    writer = csv.DictWriter(outputFile, fieldnames=columns, restval="", extrasaction='ignore',dialect='excel')

    writer.writeheader()
    for merchant in MERCHANTS:
        writer.writerow(MERCHANTS[merchant])
