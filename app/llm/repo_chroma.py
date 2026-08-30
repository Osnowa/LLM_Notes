import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


class ChromaRepository:

    def __init__(self, client):
        self.client = client  # наш асинхронный клиент
        self.embedding_function = SentenceTransformerEmbeddingFunction(  # эмбеддинг функция (БД сама векторизует данные)
            model_name="all-MiniLM-L6-v2"
        )

    async def get_collection(self):
        """Создаем или, если коллекция существует, возвращаем ее"""
        return await self.client.get_or_create_collection(
            name="notes",
            embedding_function=self.embedding_function,
        )

    async def add_note(self, user, note):
        """Добавляем данные в БД Chroma"""
        collection = await self.get_collection()

        await collection.add(
            ids=[f"{user.id}:{note.id}"],  # уникальные идентификаторы
            documents=[note.description],  # данные
            metadatas=[  # метаданные (дополнительная информация, для узкого поиска)
                {
                    "user_id": str(user.id),
                    "note_id": str(note.id),
                }
            ],
        )

    async def search(self, user, text: str, limit: int = 5):
        collection = await self.get_collection()

        return await collection.query(
            query_texts=[text],
            n_results=limit,
            where={
                "user_id": str(user.id),
            },
        )

    async def search_note_ids(
        self,
        user,
        text: str,
        limit: int = 5,
        max_distance: float = 0.5,
    ) -> list[int]:

        collection = await self.get_collection()

        result = await collection.query(
            query_texts=[text],
            n_results=limit,
            where={"user_id": str(user.id)},
        )

        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        return [
            int(metadata["note_id"])
            for metadata, distance in zip(metadatas, distances)
            if distance <= max_distance
        ]

    async def update_note(self, user, note):
        collection = await self.get_collection()

        await collection.update(
            ids=[f"{user.id}:{note.id}"],
            documents=[note.description],
            metadatas=[
                {
                    "user_id": str(user.id),
                    "note_id": str(note.id),
                }
            ],
        )

    async def delete_note(self, user, note_id: int):
        collection = await self.get_collection()

        await collection.delete(
            ids=[f"{user.id}:{note_id}"],
        )
