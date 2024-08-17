import pymongo

class Database:
    def __init__(self):
        # Replace with your actual MongoDB connection string
        self.client = pymongo.MongoClient(MONGODB_URI)
        self.db = self.client['anime_db']
        self.anime_collection = self.db['animes']

    def add_anime(self, anime_name, info_link):
        """Adds an anime to the database."""
        anime = {'name': anime_name.strip(), 'info_link': info_link.strip()}
        self.anime_collection.insert_one(anime)

    def get_anime(self, anime_name):
        """Retrieves anime information from the database."""
        anime = self.anime_collection.find_one({'name': anime_name.strip()})
        return anime
