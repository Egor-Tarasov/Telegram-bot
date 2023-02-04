class User:
    all_users = dict()

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        User.add_user(user_id=user_id, user=self)
        self.command: str = ''
        self.request_time: str = ''
        self.city: str = ''
        self.geo_id: str = ''
        self.hotels_number_to_show = 0
        self.photos_uploaded: dict = {'status': False, 'number_of_photos': 0}
        self.photos_num = 0
        self.min_price: int = 0
        self.max_price: int = 0
        self.distance_from_center: str = ''
        self.arrival_date: str = ''
        self.departure_date: str = ''
        self.check_in_date: dict = {'day': 0, 'month': 0, 'year': 0}
        self.check_out_date: dict = {'day': 0, 'month': 0, 'year': 0}
        self.list_of_hotels_id: list = []

    @classmethod
    def add_user(cls, user_id, user):
        cls.all_users[user_id] = user

    @classmethod
    def get_user(cls, user_id):
        if user_id in cls.all_users:
            return cls.all_users[user_id]
        User(user_id=user_id)
        return cls.all_users[user_id]