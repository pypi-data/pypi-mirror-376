from collections import UserDict
from collections.abc import Iterable, Iterator
import json

import httpx
from rdflib import BNode, Graph, Literal, URIRef, XSD
from rdflib.plugins.sparql import prepareQuery
from sparqlx.utils.types import _TResponseFormat, _TSPARQLBinding, _TSPARQLBindingValue


def _convert_bindings(
    response: httpx.Response,
) -> list[_TSPARQLBinding]:
    """Get flat dicts from a SPARQL SELECT JSON response."""

    try:
        json_response = response.json()
    except (
        json.JSONDecodeError
    ) as error:  # pragma: no cover ; this should be unreachable
        error.add_note("Note that convert=True requires JSON as response format.")
        raise error

    variables = json_response["head"]["vars"]
    response_bindings = json_response["results"]["bindings"]

    def _get_binding_pairs(binding) -> Iterator[tuple[str, _TSPARQLBindingValue]]:
        """Generate key value pairs from response_bindings.

        The 'type' and 'datatype' fields of the JSON response
        are examined to cast values to Python types according to RDFLib.
        """
        for var in variables:
            if (binding_data := binding.get(var, None)) is None:
                yield (var, None)
                continue

            match binding_data["type"]:
                case "uri":
                    yield (var, URIRef(binding_data["value"]))
                case "literal":
                    literal = Literal(
                        binding_data["value"],
                        datatype=binding_data.get("datatype", None),
                    )

                    # call toPython in any case for validation
                    literal_to_python = literal.toPython()

                    if literal.datatype in (XSD.gYear, XSD.gYearMonth):
                        yield (var, literal)
                    else:
                        yield (var, literal_to_python)

                case "bnode":
                    yield (var, BNode(binding_data["value"]))
                case _:  # pragma: no cover
                    assert False, "This should never happen."

    return [dict(_get_binding_pairs(binding)) for binding in response_bindings]


def _convert_graph(response: httpx.Response) -> Graph:
    _format, *_ = response.headers["content-type"].split(";")
    graph = Graph().parse(response.content, format=_format)
    return graph


def _convert_ask(response: httpx.Response) -> bool:
    return response.json()["boolean"]


class MimeTypeMap(UserDict):
    def __missing__(self, key):
        return key


bindings_format_map = MimeTypeMap(
    {
        "json": "application/sparql-results+json",
        "xml": "application/sparql-results+xml",
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
    }
)
graph_format_map = MimeTypeMap(
    {
        "turtle": "text/turtle",
        "xml": "application/xml",
        "ntriples": "application/n-triples",
        "json-ld": "application/ld+json",
    }
)


class SPARQLOperationDataMap(UserDict):
    def __init__(self, **kwargs):
        self.data = {k.replace("_", "-"): v for k, v in kwargs.items() if v is not None}


class QueryOperationParameters:
    def __init__(
        self,
        query: str,
        convert: bool | None = None,
        response_format: _TResponseFormat | str | None = None,
        version: str | None = None,
        default_graph_uri: str | Iterable[str] | None = None,
        named_graph_uri: str | Iterable[str] | None = None,
    ) -> None:
        self._query = query
        self._convert = convert
        self._query_type = prepareQuery(query).algebra.name
        self._response_format = response_format

        self.data: SPARQLOperationDataMap = SPARQLOperationDataMap(
            query=query,
            version=version,
            default_graph_uri=default_graph_uri,
            named_graph_uri=named_graph_uri,
        )
        self.headers = {"Accept": self.response_format}

    @property
    def converter(self):
        match self._query_type:
            case "SelectQuery":
                converter = _convert_bindings
            case "AskQuery":
                converter = _convert_ask
            case "DescribeQuery" | "ConstructQuery":
                converter = _convert_graph
            case _:  # pragma: no cover
                raise ValueError(f"Unsupported query type: {self._query_type}")

        return converter

    @property
    def response_format(self) -> str:
        match self._query_type:
            case "SelectQuery" | "AskQuery":
                _response_format = bindings_format_map[self._response_format or "json"]

                if self._convert and _response_format not in [
                    "application/json",
                    "application/sparql-results+json",
                ]:
                    msg = "JSON response format required for convert=True on SELECT and ASK query results."
                    raise ValueError(msg)

            case "DescribeQuery" | "ConstructQuery":
                _response_format = graph_format_map[self._response_format or "turtle"]
            case _:  # pragma: no cover
                raise ValueError(f"Unsupported query type: {self._query_type}")

        return _response_format


class UpdateOperationParameters:
    def __init__(
        self,
        update_request: str,
        version: str | None = None,
        using_graph_uri: str | Iterable[str] | None = None,
        using_named_graph_uri: str | Iterable[str] | None = None,
    ):
        self.data: SPARQLOperationDataMap = SPARQLOperationDataMap(
            update=update_request,
            version=version,
            using_graph_uri=using_graph_uri,
            using_named_graph_uri=using_named_graph_uri,
        )
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
