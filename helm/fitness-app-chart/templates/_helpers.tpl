{{/*
Expand the name of the chart.
*/}}
{{- define "fitness-app-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "fitness-app-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "fitness-app-chart.labels" -}}
helm.sh/chart: {{ include "fitness-app-chart.chart" . }}
app.kubernetes.io/name: {{ include "fitness-app-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "fitness-app-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fitness-app-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
