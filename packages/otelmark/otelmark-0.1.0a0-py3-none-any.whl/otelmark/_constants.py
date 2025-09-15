# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

from opentelemetry.sdk.resources import Resource

PACKAGE_NAME = "otelmark"
RESOURCE = Resource.create({"service.name": PACKAGE_NAME})
