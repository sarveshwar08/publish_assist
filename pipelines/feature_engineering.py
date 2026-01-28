from zenml import pipeline

from steps import feature_engineering as fe_steps

#dataset_id send at each step to maintain explicitness
@pipeline
def feature_engineering(dataset_id: str, wait_for: str | list[str] | None = None) -> list[str]:
    raw_documents = fe_steps.query_data_warehouse(dataset_id=dataset_id, after=wait_for)

    #TODO: P2 - store these cleaned docs in the mongoDB back
    cleaned_documents = fe_steps.clean_documents(raw_documents, dataset_id=dataset_id)

    embedded_documents = fe_steps.chunk_and_embed(cleaned_documents, dataset_id=dataset_id)
    last_step = fe_steps.load_to_vector_db(embedded_documents, dataset_id=dataset_id)

    return last_step.invocation_id
