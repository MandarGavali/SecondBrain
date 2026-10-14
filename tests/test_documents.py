from secondbrain.tools import documents


def test_list_documents_is_empty_before_first_upload(monkeypatch):
    def no_store():
        raise AssertionError("must not open the vector store when the collection does not exist")

    monkeypatch.setattr(documents, "collection_exists", lambda: False)
    monkeypatch.setattr(documents, "_get_vector_store", no_store)
    assert documents.list_documents() == []
