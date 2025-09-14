from typing import Optional
from pydantic import BaseModel, ValidationError
from agentlin.environment.interface import IEnvironment, IStoppableState
from agentlin.environment.state.text_state import ErrorState, TextState


class QAArguments(BaseModel):
    answer: str


class QAEnv(IEnvironment):
    def __init__(
        self,
        question: str,
        answer: str,
        info: Optional[dict[str, str]] = None,
    ):
        super().__init__()
        # 可观测状态
        self.question = question
        # 隐藏状态
        self.answer = answer

        self.info = {
            "correct": "Task completed! The answer is correct!",
            "wrong": "The answer is incorrect.",
            "invalid_state": "The state is invalid.",
            "help": """You should provide an answer: str.

<example-code>
state = env.provide_initial_state()
next_state = env(state, answer='your answer')
next_state
</example-code>""",
        }
        if info:
            self.info.update(info)

    def forward(self, s: IStoppableState, **kwargs) -> IStoppableState:
        # 一条 QA 场景下，无论是何状态，都必须得到正确回答才算完成任务
        if s.done:
            return s
        if not s.check_validity():
            return ErrorState(self.info["invalid_state"])
        try:
            args = QAArguments.model_validate(kwargs)
            answer = args.answer
            if answer == self.answer:
                return TextState(self.info["correct"], done=True)
            else:
                return TextState(self.info["wrong"])
        except ValidationError as e:
            return ErrorState(f"Invalid arguments: {e}\n\n{self.info['help']}")
        except Exception as e:
            return ErrorState(f"Unknown error: {e}\n\n{self.info['help']}")

    def provide_initial_state(self):
        return TextState(f"Question: {self.question}\n\n{self.info['help']}")


class QAListState(TextState):
    def __init__(
        self,
        question_list: list[str],
        current_index: int,
        total: int,
        done: bool = False,
    ):
        self.question_list = question_list
        self.current_index = current_index
        self.total = total
        super().__init__(self.__str__(), done)

    def check_validity(self):
        return super().check_validity() and 0 <= self.current_index < self.total

    def __str__(self):
        if not self.check_validity():
            return "Invalid State"
        return f"Current Question: {self.question_list[self.current_index]}\n\nProgress: {self.current_index}/{self.total}"


class QAListEnv(IEnvironment):
    def __init__(
        self,
        qa_list: list[tuple[str, str]],
        info: Optional[dict[str, str]] = None,
    ):
        super().__init__()
        self._qa_list = qa_list
        self.info = {
            "done": "All questions have been answered correctly. Well done!",
            "wrong": "The answer is incorrect for current question.",
            "invalid_state": "The state is invalid.",
            "type_check_error": "The state must be a QAListState.",
            "help": """You should provide an answer: str for current question.

<example-code>
state = env.provide_initial_state()  # state = question 1
next_state = env(state, answer='your answer') # next_state = question 2 if correct, else still question 1
next_state
</example-code>""",
        }
        if info:
            self.info.update(info)

    def provide_initial_state(self):
        if not self._qa_list:
            return TextState("No questions available.", done=True)
        return QAListState(
            question_list=[q for q, a in self._qa_list],
            current_index=0,
            total=len(self._qa_list),
        )

    def forward(self, s: TextState, **kwargs) -> TextState:
        if s.done:
            return s
        if not s.check_validity():
            return ErrorState(self.info["invalid_state"])
        # 必须是 QAListState 才能正常发生状态转移
        if not isinstance(s, QAListState):
            return ErrorState(self.info["type_check_error"])
        try:
            args = QAArguments.model_validate(kwargs)
            answer = args.answer
            question, correct_answer = self._qa_list[s.current_index]
            if answer == correct_answer:
                next_index = s.current_index + 1
                if next_index >= s.total:
                    return TextState(self.info["done"], done=True)
                else:
                    return QAListState(
                        question_list=[q for q, a in self._qa_list],
                        current_index=next_index,
                        total=s.total,
                    )
            else:
                return TextState(self.info["wrong"])
        except ValidationError as e:
            return ErrorState(f"Invalid arguments: {e}\n\n{self.info['help']}")
        except Exception as e:
            return ErrorState(f"Unknown error: {e}\n\n{self.info['help']}")
