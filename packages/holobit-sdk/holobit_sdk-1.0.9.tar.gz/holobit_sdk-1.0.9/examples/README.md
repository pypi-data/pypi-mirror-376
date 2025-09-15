# Ejemplos del Holobit SDK

Este directorio contiene scripts de ejemplo que demuestran diversas
capacidades del SDK y clientes para el servicio web.

- `group_evolution_demo.py`: evolución de grupos utilizando criterios de
  aptitud configurables.
- `ml_integration_example.py`: integración con flujos de ML utilizando numpy, pandas, scikit-learn y PyTorch.

## Clientes de la API

En `clients/` se incluyen pequeños programas que consumen el servicio
REST basado en FastAPI:

- `js_client.js`: cliente en JavaScript (Node.js).
- `go_client.go`: cliente en Go.

Para ejecutarlos se asume que el servicio se encuentra disponible en
`http://localhost:8000` y que las credenciales coinciden con las
variables de entorno `HOLOBIT_USER` y `HOLOBIT_PASSWORD`.

### JavaScript

```bash
npm install node-fetch
node examples/clients/js_client.js
```

### Go

```bash
go run examples/clients/go_client.go
```
