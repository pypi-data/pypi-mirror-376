"""
Copyright (c) 2025 Dan Vatca

OpenAPI schema enhancement for FastMarkDocs.

This module provides the OpenAPIEnhancer class and enhance_openapi_with_docs function
for enhancing OpenAPI schemas with documentation loaded from markdown files.
"""

import copy
import time
from typing import Any, Optional, Union

from .code_samples import CodeSampleGenerator
from .documentation_loader import MarkdownDocumentationLoader
from .endpoint_analyzer import UnifiedEndpointAnalyzer
from .exceptions import DocumentationLoadError, OpenAPIEnhancementError
from .types import (
    CodeLanguage,
    CodeSample,
    DocumentationData,
    EndpointDocumentation,
    HTTPMethod,
    OpenAPIEnhancementConfig,
    ParameterDocumentation,
    ResponseExample,
)


def _build_description_with_general_docs(
    app_title: Optional[str] = None,
    app_description: Optional[str] = None,
    original_description: Optional[str] = None,
    general_docs_content: Optional[str] = None,
) -> str:
    """
    Build a description with general docs in a standardized format.

    Args:
        app_title: Application title
        app_description: Application description
        original_description: Original description from the schema
        general_docs_content: General documentation content to include

    Returns:
        Formatted description string
    """
    description_parts = []

    # Use general docs content as the primary description if available
    if general_docs_content and general_docs_content.strip():
        description_parts.append(general_docs_content.strip())
    # Fallback to app title and description only if no general docs
    elif app_title and app_description:
        description_parts.append(f"{app_title} - {app_description}")
    elif app_title:
        description_parts.append(app_title)
    elif app_description:
        description_parts.append(app_description)
    elif original_description:
        description_parts.append(original_description)

    return "\n".join(description_parts)


def enhance_openapi_with_docs(
    openapi_schema: dict[str, Any],
    docs_directory: str,
    base_url: str = "https://api.example.com",
    include_code_samples: bool = True,
    include_response_examples: bool = True,
    code_sample_languages: Optional[list[CodeLanguage]] = None,
    custom_headers: Optional[dict[str, str]] = None,
    app_title: Optional[str] = None,
    app_description: Optional[str] = None,
    general_docs_file: Optional[str] = None,
) -> dict[str, Any]:
    """
    Enhance an OpenAPI schema with documentation from markdown files.

    Args:
        openapi_schema: Original OpenAPI schema
        docs_directory: Directory containing markdown documentation files
        base_url: Base URL for code samples
        include_code_samples: Whether to include code samples
        include_response_examples: Whether to include response examples
        code_sample_languages: List of languages for code samples
        custom_headers: Custom headers to include in code samples
        app_title: Application title
        app_description: Application description
        general_docs_file: Path to general documentation file (defaults to "general_docs.md" if found)

    Returns:
        Enhanced OpenAPI schema

    Raises:
        OpenAPIEnhancementError: If enhancement fails
    """
    try:
        # Create documentation loader
        docs_loader = MarkdownDocumentationLoader(docs_directory, general_docs_file=general_docs_file)

        # Create enhancement config
        OpenAPIEnhancementConfig(
            include_code_samples=include_code_samples,
            include_response_examples=include_response_examples,
            base_url=base_url,
            code_sample_languages=code_sample_languages or [CodeLanguage.CURL, CodeLanguage.PYTHON],
            custom_headers=custom_headers or {},
        )

        # Create enhancer and enhance schema
        enhancer = OpenAPIEnhancer(
            include_code_samples=include_code_samples,
            include_response_examples=include_response_examples,
            base_url=base_url,
            code_sample_languages=code_sample_languages,
            custom_headers=custom_headers,
        )

        documentation = docs_loader.load_documentation()
        enhanced_schema = enhancer.enhance_openapi_schema(openapi_schema, documentation)

        # Override title and description if provided, or if general docs exist
        general_docs_content = getattr(docs_loader, "_general_docs_content", None)
        if app_title or app_description or general_docs_content:
            original_description = enhanced_schema.get("info", {}).get("description", "")

            # Update title if provided and not already set properly
            # Don't override a well-formed title that already includes the app name
            current_title = enhanced_schema.get("info", {}).get("title", "")
            if app_title and not current_title.startswith(app_title):
                enhanced_schema.setdefault("info", {})["title"] = app_title

            # Build new description with general docs
            new_description = _build_description_with_general_docs(
                app_title=app_title,
                app_description=app_description,
                original_description=original_description,
                general_docs_content=general_docs_content,
            )

            if new_description:
                enhanced_schema.setdefault("info", {})["description"] = new_description

        return enhanced_schema

    except (DocumentationLoadError, FileNotFoundError, OpenAPIEnhancementError) as e:
        # Re-raise critical errors that should not be silently ignored
        raise OpenAPIEnhancementError("enhancement_failed", f"Failed to enhance OpenAPI schema: {str(e)}") from e
    except Exception:
        # Fallback to original schema on non-critical errors
        return openapi_schema


class OpenAPIEnhancer:
    """
    Enhances OpenAPI schemas with documentation from markdown files.

    This class provides comprehensive enhancement capabilities including
    code sample injection, description enhancement, example addition,
    and metadata enrichment.
    """

    def __init__(
        self,
        include_code_samples: bool = True,
        include_response_examples: bool = True,
        include_parameter_examples: bool = True,
        code_sample_languages: Optional[list[CodeLanguage]] = None,
        base_url: str = "https://api.example.com",
        server_urls: Optional[list[str]] = None,
        custom_headers: Optional[dict[str, str]] = None,
        authentication_schemes: Optional[list[str]] = None,
    ):
        """
        Initialize the OpenAPI enhancer.

        Args:
            include_code_samples: Whether to include code samples
            include_response_examples: Whether to include response examples
            include_parameter_examples: Whether to include parameter examples
            code_sample_languages: List of languages for code samples
            base_url: Base URL for code samples
            server_urls: List of server URLs
            custom_headers: Custom headers to include in code samples
            authentication_schemes: Authentication schemes to support
        """
        self.include_code_samples = include_code_samples
        self.include_response_examples = include_response_examples
        self.include_parameter_examples = include_parameter_examples
        self.code_sample_languages = code_sample_languages or [
            CodeLanguage.CURL,
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT,
        ]
        self.base_url = base_url
        self.server_urls = server_urls or [base_url]
        self.custom_headers = custom_headers or {}
        self.authentication_schemes = authentication_schemes or []

        # Initialize code sample generator
        self.code_generator = CodeSampleGenerator(
            base_url=base_url, custom_headers=self.custom_headers, code_sample_languages=self.code_sample_languages
        )

        # Will be initialized when enhance_openapi_schema is called
        self.analyzer: Optional[UnifiedEndpointAnalyzer] = None

    def enhance_openapi_schema(
        self, openapi_schema: dict[str, Any], documentation: DocumentationData
    ) -> dict[str, Any]:
        """
        Enhance an OpenAPI schema with documentation data.

        Args:
            openapi_schema: Original OpenAPI schema
            documentation: Documentation data from markdown files

        Returns:
            Enhanced OpenAPI schema

        Raises:
            OpenAPIEnhancementError: If enhancement fails
        """
        # Validate inputs
        if openapi_schema is None:
            raise OpenAPIEnhancementError("schema_validation", "OpenAPI schema cannot be None")

        if documentation is None:
            raise OpenAPIEnhancementError("documentation_validation", "Documentation data cannot be None")

        # Validate basic OpenAPI schema structure
        if not isinstance(openapi_schema, dict):
            raise OpenAPIEnhancementError("schema_validation", "OpenAPI schema must be a dictionary")

        # Check for required OpenAPI fields
        if "openapi" not in openapi_schema and "swagger" not in openapi_schema:
            raise OpenAPIEnhancementError(
                "schema_validation", "Invalid OpenAPI schema: missing 'openapi' or 'swagger' field"
            )

        if "info" not in openapi_schema:
            raise OpenAPIEnhancementError("schema_validation", "Invalid OpenAPI schema: missing 'info' field")

        try:
            # Create a deep copy to avoid modifying the original
            enhanced_schema = copy.deepcopy(openapi_schema)

            # Initialize unified analyzer for this schema
            self.analyzer = UnifiedEndpointAnalyzer(openapi_schema, base_url=self.base_url)

            # Track enhancement statistics
            stats = {"endpoints_enhanced": 0, "code_samples_added": 0, "descriptions_enhanced": 0, "examples_added": 0}
            warnings = []
            errors = []

            # Create endpoint lookup dictionary
            endpoint_lookup = {}
            for endpoint in documentation.endpoints:
                key = f"{endpoint.method.value}:{endpoint.path}"
                endpoint_lookup[key] = endpoint

            # Enhance paths
            if "paths" in enhanced_schema:
                for path, path_item in enhanced_schema["paths"].items():
                    for method, operation in path_item.items():
                        if method.upper() not in [m.value for m in HTTPMethod]:
                            continue

                        endpoint_key = f"{method.upper()}:{path}"
                        endpoint_doc = endpoint_lookup.get(endpoint_key)

                        if endpoint_doc:
                            try:
                                self._enhance_operation(operation, endpoint_doc, stats)
                                stats["endpoints_enhanced"] += 1
                            except Exception as e:
                                error_msg = f"Failed to enhance {endpoint_key}: {str(e)}"
                                errors.append(error_msg)
                        else:
                            warnings.append(f"No documentation found for {endpoint_key}")

            # Add global information
            self._enhance_global_info(enhanced_schema, documentation, stats)

            # Enhance tags with descriptions from sections
            self._enhance_sections_with_descriptions(enhanced_schema, documentation, stats)

            return enhanced_schema

        except Exception as e:
            raise OpenAPIEnhancementError("schema_root", f"Schema enhancement failed: {str(e)}") from e

    def _enhance_operation(
        self, operation: dict[str, Any], endpoint_doc: EndpointDocumentation, stats: dict[str, int]
    ) -> None:
        """
        Enhance a single OpenAPI operation with endpoint documentation.

        Args:
            operation: OpenAPI operation object
            endpoint_doc: Endpoint documentation
            stats: Statistics tracking dictionary
        """
        # Enhance summary - override auto-generated or very short summaries
        if endpoint_doc.summary:
            existing_summary = operation.get("summary", "")
            # Override if:
            # 1. No existing summary, OR
            # 2. Very short summary (likely auto-generated), OR
            # 3. Known auto-generated summaries from FastAPI
            should_override_summary = (
                not existing_summary
                or len(existing_summary) < 10
                or existing_summary.lower() in ["authorize", "get", "post", "put", "delete", "patch", "head", "options"]
            )

            if should_override_summary:
                operation["summary"] = endpoint_doc.summary
                stats["descriptions_enhanced"] += 1

        # Enhance description - prioritize rich markdown descriptions
        if endpoint_doc.description:
            existing_description = operation.get("description", "")
            # Add description if:
            # 1. No existing description, OR
            # 2. Existing description is very short (likely auto-generated), OR
            # 3. The markdown description is significantly richer (much longer)
            should_add_description = (
                not existing_description
                or len(existing_description) < 50  # Increased threshold for meaningful descriptions
                or (len(endpoint_doc.description) > len(existing_description) * 2)  # Markdown is much richer
            )

            if should_add_description:
                operation["description"] = endpoint_doc.description
                stats["descriptions_enhanced"] += 1

        # Add tags
        if endpoint_doc.sections:
            existing_tags = operation.get("tags", [])
            new_tags = [tag for tag in endpoint_doc.sections if tag not in existing_tags]
            if new_tags:
                operation["tags"] = existing_tags + new_tags

        # Add code samples
        if self.include_code_samples:
            # Always generate fresh code samples to use custom base URL and headers
            generated_samples = self.code_generator.generate_samples_for_endpoint(endpoint_doc)

            # Filter generated samples to only include requested languages
            filtered_generated = [
                sample for sample in generated_samples if sample.language in self.code_sample_languages
            ]

            # If we have existing code samples from documentation, add them too
            all_samples = list(filtered_generated)
            if endpoint_doc.code_samples:
                # Add existing samples but avoid duplicates and respect language filter
                existing_languages = {sample.language for sample in filtered_generated}
                for existing_sample in endpoint_doc.code_samples:
                    if (
                        existing_sample.language not in existing_languages
                        and existing_sample.language in self.code_sample_languages
                    ):
                        all_samples.append(existing_sample)

            self._add_code_samples_to_operation(operation, all_samples, stats)

        # Add response examples
        if self.include_response_examples and endpoint_doc.response_examples:
            self._add_response_examples_to_operation(operation, endpoint_doc.response_examples, stats)

        # Add parameter examples
        if self.include_parameter_examples and endpoint_doc.parameters:
            self._add_parameter_examples(operation, endpoint_doc.parameters, stats)

    def _add_code_samples_to_operation(
        self, operation: dict[str, Any], code_samples: list[CodeSample], stats: Optional[dict[str, int]] = None
    ) -> None:
        """
        Add code samples to an OpenAPI operation.

        Args:
            operation: OpenAPI operation object
            code_samples: List of code samples to add
            stats: Statistics tracking dictionary (optional)
        """
        if not code_samples:
            return

        openapi_samples = []
        for sample in code_samples:
            openapi_samples.append(
                {
                    "lang": sample.language.value,
                    "source": sample.code,
                    "label": sample.title or f"{sample.language.value.title()} Example",
                }
            )

        if openapi_samples:
            operation["x-codeSamples"] = openapi_samples
            if stats:
                stats["code_samples_added"] += len(openapi_samples)

    def _add_response_examples_to_operation(
        self,
        operation: dict[str, Any],
        response_examples: list[ResponseExample],
        stats: Optional[dict[str, int]] = None,
    ) -> None:
        """
        Enhanced method to add response examples supporting multiple content types to an OpenAPI operation.

        Args:
            operation: OpenAPI operation object
            response_examples: List of response examples
            stats: Statistics tracking dictionary
        """
        if "responses" not in operation:
            operation["responses"] = {}

        for example in response_examples:
            status_str = str(example.status_code)

            if status_str not in operation["responses"]:
                operation["responses"][status_str] = {"description": example.description}

            response_obj = operation["responses"][status_str]

            if example.content is not None or example.raw_content:
                if "content" not in response_obj:
                    response_obj["content"] = {}

                # Use the detected content type from the example
                content_type = getattr(example, "content_type", "application/json")

                if content_type not in response_obj["content"]:
                    response_obj["content"][content_type] = {}

                if "examples" not in response_obj["content"][content_type]:
                    response_obj["content"][content_type]["examples"] = {}

                example_key = f"example_{example.status_code}"

                # Choose the appropriate content to use in the example
                example_value: Union[str, dict[str, Any], list[Any]]
                if content_type == "application/json" and isinstance(example.content, (dict, list)):
                    example_value = example.content
                else:
                    # For non-JSON content types, use raw_content if available, otherwise content
                    if example.raw_content:
                        example_value = example.raw_content
                    elif isinstance(example.content, str):
                        example_value = example.content
                    else:
                        example_value = ""

                response_obj["content"][content_type]["examples"][example_key] = {
                    "summary": example.description,
                    "value": example_value,
                }

                # Set appropriate schema for different content types
                if "schema" not in response_obj["content"][content_type]:
                    if content_type == "application/json":
                        response_obj["content"][content_type]["schema"] = {"type": "object"}
                    elif content_type.startswith("text/"):
                        response_obj["content"][content_type]["schema"] = {"type": "string"}
                    elif content_type == "application/xml":
                        response_obj["content"][content_type]["schema"] = {"type": "string", "format": "xml"}
                    elif content_type == "application/yaml":
                        response_obj["content"][content_type]["schema"] = {"type": "string", "format": "yaml"}
                    else:
                        response_obj["content"][content_type]["schema"] = {"type": "string"}

                if stats:
                    stats["examples_added"] += 1

    def _add_parameter_examples(
        self, operation: dict[str, Any], parameters: list[ParameterDocumentation], stats: dict[str, int]
    ) -> None:
        """
        Add parameter examples to an OpenAPI operation.

        Args:
            operation: OpenAPI operation object
            parameters: List of parameter documentation
            stats: Statistics tracking dictionary
        """
        if "parameters" not in operation:
            operation["parameters"] = []

        for param_doc in parameters:
            # Find existing parameter or create new one
            existing_param = None
            for param in operation["parameters"]:
                if param.get("name") == param_doc.name:
                    existing_param = param
                    break

            if not existing_param:
                existing_param = {
                    "name": param_doc.name,
                    "in": "query",  # Default to query parameter
                    "description": param_doc.description,
                }
                operation["parameters"].append(existing_param)

            # Add example if provided
            if param_doc.example is not None:
                existing_param["example"] = param_doc.example

            # Add schema information
            if param_doc.type:
                if "schema" not in existing_param:
                    existing_param["schema"] = {}
                existing_param["schema"]["type"] = param_doc.type

            # Set required flag
            if param_doc.required is not None:
                existing_param["required"] = param_doc.required

    def _enhance_global_info(
        self, schema: dict[str, Any], documentation: DocumentationData, stats: dict[str, int]
    ) -> None:
        """
        Enhance global schema information with documentation metadata.

        Args:
            schema: OpenAPI schema
            documentation: Documentation data
            stats: Enhancement statistics
        """
        if documentation.metadata:
            info = schema.get("info", {})

            # Update title, description, version from metadata
            for key in ["title", "description", "version"]:
                if key in documentation.metadata and key not in info:
                    info[key] = documentation.metadata[key]

            schema["info"] = info

        # Add documentation enhancement statistics (only if there were enhancements)
        if (
            stats["endpoints_enhanced"] > 0
            or stats["code_samples_added"] > 0
            or stats["descriptions_enhanced"] > 0
            or stats["examples_added"] > 0
        ):
            if "info" not in schema:
                schema["info"] = {}

            schema["info"]["x-documentation-stats"] = {
                "endpoints_enhanced": stats["endpoints_enhanced"],
                "code_samples_added": stats["code_samples_added"],
                "descriptions_enhanced": stats["descriptions_enhanced"],
                "examples_added": stats["examples_added"],
                "total_endpoints": len(documentation.endpoints),
                "enhancement_timestamp": time.time(),
            }

    def _paths_match(self, openapi_path: str, doc_path: str) -> bool:
        """
        Check if OpenAPI path matches documentation path.

        Args:
            openapi_path: Path from OpenAPI schema
            doc_path: Path from documentation

        Returns:
            True if paths match
        """
        if self.analyzer:
            # Use unified analyzer for consistent path matching
            similarity = self.analyzer._calculate_path_similarity(openapi_path, doc_path)
            return similarity >= 0.8  # High confidence match
        else:
            # Fallback to original path matching logic if analyzer not available
            # Exact match first
            if openapi_path == doc_path:
                return True

            # Normalize paths by removing leading/trailing slashes
            openapi_normalized = openapi_path.strip("/")
            doc_normalized = doc_path.strip("/")

            if openapi_normalized == doc_normalized:
                return True

            # Check if paths match with different parameter names
            # e.g., /api/users/{id} should match /api/users/{user_id}
            openapi_parts = openapi_normalized.split("/")
            doc_parts = doc_normalized.split("/")

            if len(openapi_parts) != len(doc_parts):
                return False

            for openapi_part, doc_part in zip(openapi_parts, doc_parts):
                # If both are path parameters, they match regardless of name
                if (
                    openapi_part.startswith("{")
                    and openapi_part.endswith("}")
                    and doc_part.startswith("{")
                    and doc_part.endswith("}")
                ):
                    continue
                # Otherwise they must match exactly
                elif openapi_part != doc_part:
                    return False

            return True

    def _methods_match(self, openapi_method: str, doc_method: HTTPMethod) -> bool:
        """
        Check if OpenAPI method matches documentation method.

        Args:
            openapi_method: Method from OpenAPI schema
            doc_method: Method from documentation

        Returns:
            True if methods match
        """
        return openapi_method.upper() == doc_method.value

    def _enhance_operation_description(self, operation: dict[str, Any], endpoint_doc: EndpointDocumentation) -> None:
        """
        Enhance operation description with markdown formatting.

        Args:
            operation: OpenAPI operation object
            endpoint_doc: Endpoint documentation
        """
        if endpoint_doc.description:
            operation["description"] = endpoint_doc.description

    def _enhance_sections_with_descriptions(
        self, schema: dict[str, Any], documentation: DocumentationData, stats: dict[str, int]
    ) -> None:
        """
        Enhance tags in the OpenAPI schema with descriptions from documentation sections.

        Args:
            schema: OpenAPI schema
            documentation: Documentation data with section descriptions
            stats: Enhancement statistics
        """
        # Collect all unique tags from endpoints
        all_tags = set()
        if "paths" in schema:
            for path_item in schema["paths"].values():
                for operation in path_item.values():
                    if isinstance(operation, dict) and "tags" in operation:
                        all_tags.update(operation["tags"])

        # Create or enhance tags section only if we have section descriptions
        if all_tags and documentation.section_descriptions:
            if "tags" not in schema:
                schema["tags"] = []

            # Convert existing tags to a dict for easier lookup
            existing_tags = {tag["name"]: tag for tag in schema["tags"] if isinstance(tag, dict) and "name" in tag}

            # Add or enhance tags with descriptions from sections
            for tag_name in all_tags:
                if tag_name in documentation.section_descriptions:
                    tag_description = documentation.section_descriptions[tag_name]

                    if tag_name in existing_tags:
                        # Update existing tag with description if it doesn't have one
                        if "description" not in existing_tags[tag_name]:
                            existing_tags[tag_name]["description"] = tag_description
                            stats["descriptions_enhanced"] += 1
                    else:
                        # Add new tag with description from section
                        schema["tags"].append({"name": tag_name, "description": tag_description})
                        stats["descriptions_enhanced"] += 1
