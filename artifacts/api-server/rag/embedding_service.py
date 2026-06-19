import os
from openai import OpenAI


class OpenAIEmbeddingService:
    def __init__(self):
        # Look for dedicated embedding variables first, fallback to standard OpenAI
        self.api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("EMBEDDING_BASE_URL")
        
        # Initialize client with dedicated base URL override if supplied
        self.client = OpenAI(api_key=self.api_key, base_url=base_url) if self.api_key else None
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text chunk."""
        if not self.client:
            # Fallback mock embedding if API key is not configured (e.g. during offline testing)
            if "gemini-embedding" in self.model:
                dim = 3072
            elif "text-embedding-004" in self.model:
                dim = 768
            else:
                dim = 1536
            return [0.0] * dim

        response = self.client.embeddings.create(
            input=[text.replace("\n", " ")], model=self.model
        )
        return response.data[0].embedding

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of text chunks."""
        if not self.client or not texts:
            if "gemini-embedding" in self.model:
                dim = 3072
            elif "text-embedding-004" in self.model:
                dim = 768
            else:
                dim = 1536
            return [[0.0] * dim for _ in texts]

        sanitized = [t.replace("\n", " ") for t in texts]
        response = self.client.embeddings.create(input=sanitized, model=self.model)
        return [data.embedding for data in response.data]
