"""Example of generating a raw dataset using the OpenAI API"""

# For asynchronous dataset generation
# import asyncio
import os

from synthgenai import (
    DatasetConfig,
    DatasetGeneratorConfig,
    LLMConfig,
    RawDatasetGenerator,
)

os.environ["OPENAI_API_KEY"] = ""

os.environ["HF_TOKEN"] = ""

if __name__ == "__main__":
    # Defining the LLM used for generating the dataset and the settings of the LLM
    llm_config = LLMConfig(model="gpt-5", temperature=0.5)

    # Defining the dataset configuration, the topic of the dataset, the domains, the language, the additional description, and the number of entries
    dataset_config = DatasetConfig(
        topic="Medical Diagnosis",
        domains=["Healthcare", "Medicine"],
        language="English",
        additional_description="This dataset must be more focused on medical diagnosis and healthcare applications.",
        num_entries=1000,
    )

    # Defining the dataset Hugging Face repository name
    hf_repo_name = (
        "{organization_or_account_name}/artificial-intelligence-in-healthcare"
    )

    # Defining the dataset generator configuration
    dataset_generator_config = DatasetGeneratorConfig(
        dataset_config=dataset_config, llm_config=llm_config
    )

    # Defining the raw dataset generator based on the dataset generator configuration
    dataset_generator = RawDatasetGenerator(dataset_generator_config)

    # Generating the dataset
    dataset = dataset_generator.generate_dataset()

    # Generating the dataset asynchronously
    # dataset = asyncio.run(dataset_generator.agenerate_dataset())

    # Saving the dataset to the locally and to the Hugging Face repository
    dataset.save_dataset(
        hf_repo_name=hf_repo_name,
    )
