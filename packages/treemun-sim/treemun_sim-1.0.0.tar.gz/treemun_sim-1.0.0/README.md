# treemun: a growth and yield simulator for chilean plantation forest

A Python package that implements a discrete-time simulation framework for evaluating management policies in Pinus radiata and Eucalyptus globulus forest stands.

## install

```bash
pip install treemun-sim
```

## basic use

```python
import treemun_sim as tm

# simulation with default parameters
bosque, resumen, biomasa_final, biomasa_estimada = tm.simular_bosque()

# custom simulation
bosque, resumen, biomasa_final, biomasa_estimada = tm.simular_bosque(
    policies_pino=[(9, 18), (10, 20), (11, 22)],
    policies_eucalyptus=[(9,), (10,), (11,)],
    horizonte=25,
    num_rodales=50,
    semilla=1234
)

print(f"Se generaron {len(bosque)} combinaciones rodal-política")
```

## parameters

- **policies_pino**: Lista de políticas para pino `[(edad_raleo, edad_cosecha), ...]`
- **policies_eucalyptus**: Lista de políticas para eucalipto `[(edad_cosecha,), ...]`
- **horizonte**: Horizonte temporal en años (default: 30)
- **num_rodales**: Número de rodales a generar (default: 100)
- **semilla**: Semilla para reproducibilidad (default: 5555)

## outputs

- **bosque**: Lista de DataFrames con simulación período a período
- **resumen**: Lista de diccionarios con información de cada rodal
- **biomasa_final**: Diccionario con biomasa al final del horizonte
- **biomasa_estimada**: Diccionario optimizado para algoritmos de optimización

## supported species

- **Pinus**: Con políticas de raleo y cosecha
- **Eucalyptus**: Con políticas de cosecha únicamente

## author

Felipe Ulloa-Fierro

## license

MIT



