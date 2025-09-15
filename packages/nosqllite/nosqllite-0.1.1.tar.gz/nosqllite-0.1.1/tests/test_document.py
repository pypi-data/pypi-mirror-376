import nosqllite
import os 
import datetime

DB_NAME = "./tests/my-nosql-lite-db"

def get_db() -> nosqllite.Database:
    global DB_NAME
    if not os.path.exists(DB_NAME):
        db = nosqllite.Database.new(DB_NAME)
    else: 
        db = nosqllite.Database(DB_NAME)
    DB_NAME = os.path.abspath(DB_NAME)
    return db

def test_document_name():
    global DB_NAME
    db = get_db()
    doc_name = f"test-doc-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    doc = db.add_document(doc_name)
    assert doc.name == doc_name
    assert doc.file_path == DB_NAME + "/" + doc_name + ".json"
    doc.delete()
    del doc

def test_document_data():
    global DB_NAME
    db = get_db()
    doc_name = f"test-doc-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    doc = db.add_document(doc_name)

    doc.data["some_key"] = [1,2]
    doc["some_key"].append(3)
    assert doc.data == {"some_key":[1,2,3]}
    
    doc.delete()
    del doc



def test_document_synt():
    global DB_NAME
    db = get_db()
    doc_name = f"test-doc-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    doc = db.add_document(doc_name)

    doc.data["some_key"] = [1,2]
    doc.save()

    _, d = nosqllite.Document._read(DB_NAME + "/" + doc_name + ".json")
    assert d == doc.data
    
    doc.delete()
    del doc


def test_document_metadata():
    global DB_NAME
    db = get_db() 
    doc_name = f"test-doc-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    doc = db.add_document(doc_name) 
    doc.data = [1,2]
    doc.set_metadata()
    expected_metadata_keys = ["timestamp", "datahash", ] 
    
    assert list(doc.metadata.keys()) == expected_metadata_keys

    doc.delete()
    del doc


def test_document_clean_up(): 
    global DB_NAME
    db = get_db() 
    db.delete()
    assert not os.path.isdir(DB_NAME)