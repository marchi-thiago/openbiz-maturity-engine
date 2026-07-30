import builtins
import main

# Mocka a função input para sempre retornar string vazia
builtins.input = lambda prompt="": ""

print("🚀 Iniciando teste automático do MVP (usando dados Mockados)...")
main.main()
print("✅ Teste finalizado!")
