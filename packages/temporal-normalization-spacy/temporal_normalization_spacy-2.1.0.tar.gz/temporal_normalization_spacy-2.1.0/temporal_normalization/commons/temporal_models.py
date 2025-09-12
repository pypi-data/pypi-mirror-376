import json

from py4j.java_gateway import JavaObject, JavaGateway

from temporal_normalization.commons.temporal_types import TemporalType


class TemporalExpression:
    """
    A model representing a temporal expression, extracted and processed
    from a Java object.

    Attributes:
        is_valid (bool): A flag that specifies whether the text processed
            through timespan-normalization library is a temporal expression.
        input_value (str or None): The original temporal expression before processing.
        prepared_value (str or None): The temporal expression after processing.
        time_series (list[TimeSeries]): The list of normalized temporal expressions.
        matches (list[str]): A unique list of matched values found in the normalized
            entities.
    """

    def __init__(self, java_object: JavaObject):
        serialize = java_object.serialize()
        json_obj = json.loads(serialize)

        # fmt: off
        self.is_valid = TemporalExpression.is_valid_json(json_obj)
        self.input_value: str | None = json_obj["inputValue"] if self.is_valid else None
        self.prepared_value: str | None = json_obj["preparedValue"] if self.is_valid else None
        self.time_series: list[TimeSeries] = [
            TimeSeries(item, self.input_value, self.prepared_value) for item in json_obj["timeSeries"]
        ] if self.is_valid else []
        self.matches: list[str] = list(
            set(
                [
                    matched_value
                    for ts in self.time_series
                    for matched_value in ts.matches
                ]
            )
        )
        # fmt: on

    def __str__(self):
        if self.input_value is None:
            return "TemporalExpression(None)"

        return f"TemporalExpression({self.input_value})"

    def __repr__(self):
        return self.input_value

    @staticmethod
    def is_valid_json(json_obj) -> bool:
        return "inputValue" in json_obj and "timeSeries" in json_obj


def extract_temporal_expressions(
    gateway: JavaGateway, text: str
) -> list[TemporalExpression]:
    """
    Extracts valid temporal expressions from the given text using the Java temporal
    normalization gateway.

    Args:
        gateway (JavaGateway): Active Py4J gateway connected to the Java temporal
            normalization process.
        text (str): Input text from which to extract temporal expressions.

    Returns:
        list[TemporalExpression]: A list containing valid temporal expressions.
    """

    expressions: list[TemporalExpression] = []
    java_object = gateway.jvm.ro.webdata.normalization.timespan.ro.TimeExpression(text)
    temporal_expression = TemporalExpression(java_object)

    if temporal_expression.is_valid:
        expressions.append(temporal_expression)

    return expressions


class TimeSeries:
    """
    A data structure representing a temporal expression that has been normalized
    into a list of periods and temporal edges.

    Attributes:
        input_value (str or None): The original temporal expression before processing.
        prepared_value (str or None): The temporal expression after processing.
        edges (list[EdgeModel]): A list of temporal intervals represented as edges.
        periods (list[DBpediaModel]): A list of normalized DBpedia entities
            extracted from the expression.
        matches (list[str]): A unique list of matched values found in the normalized
            entities.
    """

    def __init__(self, data: dict, input_value: str, prepared_value: str):
        self.input_value = input_value
        self.prepared_value = prepared_value
        self.edges: EdgeModel = EdgeModel(data["edges"]) if "edges" in data else None
        self.periods: list[DBpediaModel] = (
            [DBpediaModel(item) for item in data["periods"]]
            if "periods" in data
            else []
        )
        self.matches: list[str] = list(
            set([item.matched_value for item in self.periods])
        )

    def __repr__(self):
        return f"TimeSeries(edges={self.edges}, periods={self.periods})"

    def serialize(self, indent: str = ""):
        # fmt: off
        return (
            f"{indent}Edges: {self.edges}\n"
            f"{indent}Periods: {self.periods}"
        )
        # fmt: on


class DBpediaModel:
    """
    A model representing an entity from DBpedia, storing key attributes related
    to the entity.

    Attributes:
        uri (str): The unique identifier (URI) of the DBpedia entity.
        label (str): A human-readable name for the entity.
        matched_value (str): The original matched value from the input data.
        matched_type (TemporalType or None): The temporal type of the entity,
        if applicable.
    """

    def __init__(self, data: dict):
        self.uri: str = data["uri"] if "uri" in data else None
        self.label: str = data["label"] if "label" in data else None
        self.matched_value: str = (
            data["matchedValue"] if "matchedValue" in data else None
        )
        try:
            self.matched_type: TemporalType = (
                TemporalType(data["matchedType"]) if "matchedType" in data else None
            )
        except ValueError:
            self.matched_type = None

    def __repr__(self):
        return f"DBpediaModel(label={self.label}, matched_value={self.matched_value})"

    def serialize(self, indent: str = ""):
        matched_type = self.matched_type.value if self.matched_type else None

        return (
            f"{indent}Matched value: {self.matched_value}\n"
            f"{indent}Matched Type: {matched_type}\n"
            f"{indent}Normalized label: {self.label}\n"
            f"{indent}DBpedia uri: {self.uri}"
        )


class EdgeModel:
    """
    A model representing time interval represented as DBpedia entities.
    This edge represents the starting and ending points of a time period.

    Attributes:
        start (DBpediaModel): The starting entity of the time period.
        end (DBpediaModel): The ending entity of the time period.
    """

    def __init__(self, data: dict):
        self.start: DBpediaModel = (
            DBpediaModel(data["start"]) if "start" in data else None
        )
        self.end: DBpediaModel = DBpediaModel(data["end"]) if "end" in data else None

    def __repr__(self):
        return f"EdgeModel(start={self.start}, end={self.end})"

    def serialize(self, indent: str = ""):
        start = self.start.serialize("\t")
        end = self.end.serialize("\t")

        return f"{indent}Start time:\n{start}\n" f"{indent}End time:\n{end}"
