# PhoneVerify Mobile Money Cameroun

> **Package Python de validation des numéros de téléphone mobile money pour le Cameroun**  
> Validation instantanée, détection d'opérateurs et conversion de formats pour MTN et Orange

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)


## **Le Problème**

Le Cameroun est le leader du mobile money en zone CEMAC avec 96% des transactions. Cependant, **0,5% des transactions échouent** à cause d'erreurs de format de numéros, représentant **2,5 milliards FCFA bloqués** annuellement.

**Ce que j'ai constaté:**
- ❌ Formats inconsistants entre applications
- ❌ 50+ startups fintech développent CHACUNE leur propre validateur  
- ❌ Confusion entre opérateurs (MTN vs Orange)
- ❌ Maintenance coûteuse lors de changements réglementaires
- ❌ Barrière à l'entrée pour nouvelles startups

**Solution :** Package Open Source unifié pour l'écosystème fintech camerounais 🇨🇲

---

## **Installation Rapide**

```bash
pip install phoneverify-cameroon
```

```python
import phoneverify_cameroon as pv

# Validation simple
result = pv.validate_phone("677123456")
print(f"Valid: {result['is_valid']}")          # True
print(f"Opérateur: {result['operator']}")      # MTN Mobile Money
print(f"Format E164: {result['formatted']['E164']}")  # +237677123456
```

---

## **Fonctionnalités**

- ✅ Validation format camerounais
- ✅ Détection automatique opérateur (MTN/Orange)  
- ✅ 39 préfixes supportés (19 MTN + 20 Orange)
- ✅ Gestion multiple formats d'entrée

### **Fonctions Principales**
- **`validate_phone()`** - Validation complète avec détails
- **`detect_operator()`** - Détection d'opérateur uniquement  
- **`format_phone()`** - Conversion de formats
- **`bulk_validate()`** - Validation en masse
- **`get_supported_operators()`** - Liste des opérateurs

### **Formats Supportés**
- **E164** : `+237677123456` (international)
- **National** : `0677123456` (format local officiel)
- **Local** : `677123456` (format interne)
- **Display** : `677 12 34 56` (affichage utilisateur)

---

## 📚 **Documentation**

### **Validation Simple**

```python
import phoneverify_cameroon as pv

# Validation d'un numéro MTN
result = pv.validate_phone("677123456")
print(result)
```

**Résultat :**
```json
{
  "original_input": "677123456",
  "is_valid": true,
  "operator": "MTN Mobile Money",
  "operator_code": "MTN", 
  "prefix": "677",
  "cleaned_number": "677123456",
  "formatted": {
    "E164": "+237677123456",
    "national": "0677123456", 
    "local": "677123456",
    "display": "677 12 34 56"
  },
  "error": null
}
```

### **Gestion des Formats d'Entrée**

Le package accepte **tous les formats** couramment utilisés :

```python
# Tous ces formats sont valides pour le même numéro
formats = [
    "677123456",           # Local
    "0677123456",          # National
    "+237677123456",       # International
    "+237 677 123 456",    # Avec espaces
    "237-677-123-456",     # Avec tirets
    "(677) 123-456",       # Format parenthèses
]

for phone in formats:
    result = pv.validate_phone(phone)
    print(f"{phone} -> {result['is_valid']}")  # Tous True
```

### **Détection d'Opérateurs**

```python
# Détection simple
operator = pv.detect_operator("677123456")
print(operator)  # "MTN Mobile Money"

operator = pv.detect_operator("655123456") 
print(operator)  # "Orange Money"

# Opérateur inconnu
operator = pv.detect_operator("600123456")
print(operator)  # None
```

### **Conversion de Formats**

```python
# Conversion vers différents formats
number = "677123456"

e164 = pv.format_phone(number, "E164")      # "+237677123456"
national = pv.format_phone(number, "national")  # "0677123456"
display = pv.format_phone(number, "display")    # "677 12 34 56"
```

### **Traitement en Masse**

```python
# Validation de plusieurs numéros
numbers = ["677123456", "655987654", "invalid123", "680555666"]

# Validation bulk
results = pv.bulk_validate(numbers)
for result in results:
    print(f"{result['original_input']}: {result['is_valid']}")

# Détection d'opérateurs avec regroupement
detection = pv.detect_operators_bulk(numbers)
print(f"MTN: {len(detection['MTN'])} numéros")
print(f"Orange: {len(detection['Orange'])} numéros") 
print(f"Invalides: {len(detection['Invalid'])} numéros")

# Conversion en masse
conversions = pv.convert_format_bulk(numbers, "E164")
for conv in conversions:
    if conv['converted']:
        print(f"{conv['original']} -> {conv['converted']}")
```

### **Informations sur les Opérateurs**

```python
# Liste des opérateurs supportés
operators = pv.get_supported_operators()
for op in operators:
    print(f"{op['name']}: {len(op['prefixes'])} préfixes")
    print(f"Code: {op['code']}")
    print(f"Préfixes: {op['prefixes'][:5]}...")  # Premiers 5
    print()

# Tous les préfixes supportés  
all_prefixes = pv.get_supported_prefixes()
print(f"Total: {len(all_prefixes)} préfixes supportés")
print(f"MTN commence par: 65x, 67x, 68x")
print(f"Orange commence par: 64x, 65x, 68x, 69x")
```

---




## 📊 **Opérateurs et Préfixes Supportés**

### **MTN Mobile Money (19 préfixes)**
```
650, 651, 652, 653, 654
670, 671, 672, 673, 674, 675, 676, 677, 678, 679  
680, 681, 682, 683
```

### **Orange Money (20 préfixes)**  
```
640
655, 656, 657, 658, 659
686, 687, 688, 689
690, 691, 692, 693, 694, 695, 696, 697, 698, 699
```

**Total : 39 préfixes actifs**
---


## 🤝 **Contribution**

Donner un coup de main.. 🙃

1. **Fork** le projet sur GitHub
2. **Créer** une branche feature (`git checkout -b feature/amazing`) 
3. **Commit** (`git commit -m 'Add amazing feature'`)
4. **Push** (`git push origin feature/amazing`)
5. **Ouvrir** une Pull Request

---

## 📄 **Licence**

MIT License - Utilisation libre pour projets commerciaux et open source.

---



**Développé avec ❤️ pour l'écosystème fintech camerounais**

---
