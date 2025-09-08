# MPCG: Multi-Round Persona-Conditioned Generation for Modeling the Evolution of Misinformation with LLMs

## Abstract
Misinformation evolves as it spreads, shifting in language, framing, and moral emphasis to adapt to new audiences. However, current misinformation detection approaches implicitly assume that misinformation is static. We introduce **MPCG**, a multi-round, persona-conditioned framework that simulates how claims are iteratively reinterpreted by agents with distinct ideological perspectives. Our approach uses an uncensored large language model (LLM) to generate persona-specific claims across multiple rounds, conditioning each generation on outputs from the previous round, enabling the study of misinformation evolution. We evaluate the generated claims through human and LLM-based annotations, cognitive effort metrics (readability, perplexity), emotion evocation metrics (sentiment analysis, morality), clustering, and downstream classification. Results show strong agreement between human and GPT-4o-mini annotations, with higher divergence in fluency judgments. Generated claims require greater cognitive effort than the original claims and consistently reflect persona-aligned emotional and moral framing. Clustering and cosine similarity analyses confirm semantic drift across rounds while preserving topical coherence. Classification results reveal that commonly used misinformation detectors experience macro-F1 performance drops of up to 50%.

## Environment Setup
1. Create an environment with Python 3.10.

Install dependencies with pip:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install numpy==1.24.4
pip install transformers==4.31.0
```

2. Copy the `.env.sample` file as `.env` and add your keys.
```
HF_TOKEN="Enter your HuggingFace Token"
OPENAI_KEY="Enter your OpenAI API Key"
```

## MPCG Framework
### Prepare the **Dataset** for the Framework
Please run all of these commands in sequence to prepare the dataset.

1. Scrape articles from PolitiFact. (Adjust --page_limit to ensure you have enough True datapoints to use for the dataset. The default is 50)
```bash
python ./data_pipeline/politifact_link_extractor.py 
```

2. Extract all of the information from the extracted HTMLs.
```bash
python ./data_pipeline/politifact_articles_extractor.py
```

3. Format all the extracted details
```bash
python ./data_pipeline/politifact_articles_formatter.py
```

4. Annotation request to GPT-4o-mini
```bash
python ./data_pipeline/politifact_extractor_openai_batch_request.py
```

5. Retrieve annotation output from GPT-4o-mini.
```bash
python ./data_pipeline/politifact_extractor_openai_batch_check.py
```

6. Format all the annotation output from GPT-4o-mini
```bash
python ./data_pipeline/format_batch_outputs.py
```

7. Prepare Train, Dev and Test dataset 
```bash
python ./data_pipeline/train_dev_test.py
```

### Run MPCG
After the dataset preparation process, run these steps. (We took about 2 days to do all of these without crashing on Google Colab A100 40 GB)

1. Misinformation Generation
```bash
python ./mpcg/role_playing_misinformation_generation_cuda.py
```

2. Misinformation Labeling
```bash
python ./mpcg/role_playing_misinformation_labelling_cuda.py
```

## MPCG Evaluations
### Prepare Generated Dataset
1. After running MPCG, run the command below to prepare a generated dataset that uses the generated outputs.
```bash
python ./evaluation/prepare_evaluation_dataset.py
```

### Classification
1. Finetune Encoder Models
```bash
bash ./scripts/finetune_encoders.sh
```

2. Testing Encoder and Decoder Models
```bash
bash ./scripts/evaluate/encoder.sh
bash ./scripts/evaluate/decoder.sh
bash ./scripts/evaluate/gpt.sh
```

### EQA Tool
We use the tool provided by [Thibault et.al (2025)](https://github.com/ComplexData-MILA/misinfo-datasets).
Please follow the directions in the mentioned repo.
Here we show our results with 300 claims based on 20 unique PolitiFact articles.

```
(base) ➜  misinfo-datasets git:(main) ✗ source .env && \
uv run -m misinfo_data_eval.entrypoint \
--source_dataset_path csv://dataset/eqa/data.csv \
--evaluate_feasibility \
--evaluator_model_name gpt-4o-mini-2024-07-18 \
--max_concurrency 32 \
--limit 300
len(dataset): 300
100%|████████████████████████████████████| 300/300 [00:21<00:00, 13.94it/s]
100%|████████████████████████████████████| 300/300 [00:26<00:00, 11.28it/s]
Evaluating Feasibility: 100%|████████████████| 2/2 [00:48<00:00, 24.06s/it]
{
  "feasible, no search required": 28,
  "feasible, requires search": 203,
  "not feasible even with search": 59,
  "null": 10
}
```

### Metrics, Claim Analysis & Visualizations
Use `visualization.ipynb` to get Claim Analysis and Classification Results Visualizations.
