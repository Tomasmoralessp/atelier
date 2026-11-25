# Arquitectura del Sistema

## Capas del Sistema

El sistema está organizado en varias capas que interactúan entre sí para proporcionar la funcionalidad completa:

### 1. Frontend (React + Tauri)
- Interfaz de usuario desarrollada con React y TypeScript
- Utiliza Tauri para crear aplicaciones nativas para macOS, Windows y Linux
- Se comunica con el backend a través de una API REST

### 2. Backend (FastAPI)
- Servidor web construido con FastAPI
- Gestiona la lógica de negocio y la comunicación con bases de datos
- Proporciona endpoints para la interfaz de usuario

### 3. Pipeline de Clasificación
- Procesamiento de imágenes mediante modelos de aprendizaje profundo
- Implementación de técnicas de computer vision para el análisis de imágenes
- Uso de modelos preentrenados con optimización de rendimiento

### 4. Base de Datos (PostgreSQL)
- Almacenamiento persistente de datos de usuarios, imágenes y clasificaciones
- Gestión de relaciones entre diferentes entidades del sistema

## Optimizaciones Específicas

### Cambio de Modelo
- Se ha cambiado el modelo base de ViT-B-32 a RN50 (ResNet-50)
- Esta optimización mejora el rendimiento y reduce el uso de recursos

### Caché de Embeddings
- Implementación de un sistema de caché para embeddings previamente calculados
- Reducción del tiempo de procesamiento al evitar cálculos redundantes

### Lazy Loading
- Carga diferida de componentes y recursos
- Mejora la experiencia de usuario al reducir el tiempo inicial de carga

### Tamaño de Batch
- Optimización del tamaño de los lotes de procesamiento para mejorar el rendimiento
- Ajuste dinámico según el recurso disponible

### Optimizaciones de Docker
- Imágenes optimizadas para reducir el tamaño y el tiempo de despliegue
- Uso de multi-stage builds para reducir la superficie de ataque