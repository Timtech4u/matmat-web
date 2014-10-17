import math

INITIAL_DIFFICULTY = 0
INITIAL_TIME_INTENSITY = 2
INITIAL_SKILL = 0


class EloModel():
    def __init__(self, data_provider):
        self.data = data_provider

    @staticmethod
    def expected_response(user_skill, difficulty, question_type):
        if question_type == 'c':
            return 1. / (1 + math.exp(difficulty - user_skill))
        if question_type == 't':
            return -(user_skill - difficulty)

    @staticmethod
    def compute_user_skill_delta(response, expected_response, question_type, level):
        K = 0.7
        K_correct = 1
        K_incorrect = 0.5
        delta = 0

        if question_type == 'c':
            if response == 1:
                delta = K_correct * (response - expected_response)
            else:
                delta = K_incorrect * (response - expected_response)
        if question_type == 't':
            delta = K * (expected_response - response)

        level_coef = 1. / 3 ** (4 - level)   # level is in range [1,4]

        return level_coef * delta

    @staticmethod
    def compute_difficulty_delta(response, expected_response, first_attempts_count, question_type):
        ALPHA = 1.0
        DYNAMIC_ALPHA = 0.05
        K = ALPHA / (1 + DYNAMIC_ALPHA * (first_attempts_count - 1))
        delta = 0

        if question_type == 'c':
            delta = K * (expected_response - response)  # that is K * ((1 - response) - (1 - expected_response))
        if question_type == 't':
            delta = K * (response - expected_response)

        return delta

    @staticmethod
    def compute_time_intensity_delta(response_time, time_intensity, first_attempts_count):
        ALPHA = .4
        DYNAMIC_ALPHA = 0.05
        K = ALPHA / (1 + DYNAMIC_ALPHA * (first_attempts_count - 1))
        if response_time == 0: response_time = 1        # hack for zero response times
        delta = K * (math.log(response_time) - time_intensity)

        return delta

    def response(self, answer, question, time_intensity, question_type="c"):
        TIME_PENALTY_SLOPE = 0.8    # smaller for larger slope

        if question_type == 'c':
            if not self.data.get_correctness(answer):
                return 0
            else:
                solving_time = self.data.get_solving_time(answer)
                expected_solving_time = math.exp(time_intensity)
                if expected_solving_time > solving_time:
                    response = 1
                else:
                    response = TIME_PENALTY_SLOPE ** ((solving_time / expected_solving_time) - 1)
                print response, expected_solving_time, solving_time
                return response

        if question_type == 't':
            return math.log(self.data.get_solving_time(answer))

    def get_user_skill(self, user, skill):
        """
        compute absolute and relative skill of user
        @return: absolute skill, relative skill
        """

        parent_skill = self.data.get_parent_skill(skill)
        user_skill = self.data.get_user_skill(user, skill)

        # stop recursion on root
        if parent_skill is None:
            if user_skill is None:
                return INITIAL_SKILL, INITIAL_SKILL
            else:
                return user_skill, user_skill

        # initialize skill if does not exist
        if user_skill is None:
            user_skill = 0

        parent_user_skill, _ = self.get_user_skill(user, parent_skill)
        return user_skill + parent_user_skill, user_skill

    def update(self):
        """
        update model using answer provided by data provider
        """
        # get data
        answer = self.data.get_answer()
        user = self.data.get_user(answer)
        question = self.data.get_question(answer)
        question_type = self.data.get_question_type(question)
        leaf_skill = self.data.get_skill(question)
        original_user_skill, _ = self.get_user_skill(user, leaf_skill)

        # get question difficulty
        difficulty = self.data.get_difficulty(question)
        if difficulty is None:
            difficulty = INITIAL_DIFFICULTY
            self.data.set_difficulty(question, difficulty)

        # get and update time intensity
        time_intensity = self.data.get_time_intensity (question)
        if time_intensity is None:
            time_intensity = INITIAL_TIME_INTENSITY
            self.data.set_time_intensity(question, time_intensity)


        time_intensity += self.compute_time_intensity_delta(
                self.data.get_solving_time(answer),
                time_intensity,
                self.data.get_first_attempts_count(question),
            )
        self.data.set_time_intensity(question, time_intensity)

        response = self.response(answer, question, time_intensity, question_type)

        # update skills
        level = 0   # level of updated skill
        for skill in self.get_ancestor_skills(leaf_skill):
            level += 1
            user_skill, relative_user_skill = self.get_user_skill(user, skill)
            expected_response = self.expected_response(
                                user_skill=user_skill,
                                difficulty=difficulty,
                                question_type=question_type
                            )

            user_skill_delta = self.compute_user_skill_delta(response, expected_response, question_type, level)
            self.data.set_user_skill(user, skill, relative_user_skill + user_skill_delta)

        # update difficulty and time intensity
        expected_response = self.expected_response(
                                    user_skill=original_user_skill,
                                    difficulty=difficulty,
                                    question_type=question_type
                                )

        if self.data.is_first_attempt(answer):
            difficulty_delta = self.compute_difficulty_delta(
                response,
                expected_response,
                self.data.get_first_attempts_count(question),
                question_type
            )
            self.data.set_difficulty(question, difficulty + difficulty_delta)

    def get_ancestor_skills(self, skill):
        """
        get all ancestor skills in tree (itself included)
        skills are ordered from root to leaf
        """
        skills = []
        tmp_skill = skill
        while tmp_skill is not None:
            skills = [tmp_skill] + skills
            tmp_skill = self.data.get_parent_skill(tmp_skill)
        return skills