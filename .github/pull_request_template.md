## 📋 Descrição

<!-- Descreva brevemente as mudanças implementadas neste PR -->

## 🔄 Tipo de Mudança

<!-- Marque o tipo de mudança com [x] -->

- [ ] 🐛 Bug fix (correção que resolve um problema)
- [ ] ✨ Nova funcionalidade (mudança que adiciona funcionalidade)
- [ ] 💥 Breaking change (correção ou funcionalidade que causa mudança incompatível)
- [ ] 📚 Documentação (mudanças apenas na documentação)
- [ ] 🎨 Estilo (formatação, ponto e vírgula ausente, etc; sem mudança de código)
- [ ] ♻️ Refatoração (mudança de código que não corrige bug nem adiciona funcionalidade)
- [ ] ⚡ Performance (mudança que melhora performance)
- [ ] ✅ Testes (adição ou correção de testes)
- [ ] 🔧 Chore (mudanças no processo de build, ferramentas auxiliares, etc)

## 🧪 Como Testar

<!-- Descreva os passos para testar as mudanças -->

1. 
2. 
3. 

## 📸 Screenshots (se aplicável)

<!-- Adicione screenshots para mudanças visuais -->

## ✅ Checklist

<!-- Marque todos os itens aplicáveis com [x] -->

### Código
- [ ] Meu código segue as diretrizes de estilo do projeto
- [ ] Realizei uma auto-revisão do meu código
- [ ] Comentei meu código, especialmente em áreas difíceis de entender
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que minha correção é efetiva ou que minha funcionalidade funciona

### Backend (Python)
- [ ] Executei `flake8 backend/` sem erros
- [ ] Executei `black --check backend/` sem erros
- [ ] Executei `isort --check-only backend/` sem erros
- [ ] Executei `pytest backend/tests/` e todos os testes passaram
- [ ] Executei `bandit -r backend/` sem problemas críticos
- [ ] A cobertura de testes não diminuiu significativamente

### Frontend (TypeScript/React)
- [ ] Executei `npm run lint` sem erros
- [ ] Executei `npm run format:check` sem erros
- [ ] Executei `npm run type-check` sem erros
- [ ] Executei `npm test` e todos os testes passaram
- [ ] Executei `npm run build` com sucesso
- [ ] A cobertura de testes não diminuiu significativamente

### Documentação
- [ ] Atualizei a documentação relevante
- [ ] Atualizei comentários no código quando necessário
- [ ] Adicionei/atualizei docstrings para novas funções/classes

### CI/CD
- [ ] O pipeline CI passou completamente
- [ ] Não há conflitos de merge
- [ ] O branch está atualizado com a branch base

## 🔗 Issues Relacionadas

<!-- Referencie issues relacionadas usando "Closes #123" ou "Fixes #123" -->

Closes #
Fixes #
Related to #

## 📝 Notas Adicionais

<!-- Adicione qualquer informação adicional relevante -->

## 🔍 Revisão

<!-- Para os revisores -->

### Pontos de Atenção
- [ ] Verificar se a lógica de negócio está correta
- [ ] Verificar se os testes cobrem os casos edge
- [ ] Verificar se não há vazamentos de memória
- [ ] Verificar se as mudanças não afetam a performance
- [ ] Verificar se a segurança não foi comprometida

### Checklist do Revisor
- [ ] O código está limpo e bem estruturado
- [ ] Os testes são adequados e passam
- [ ] A documentação está atualizada
- [ ] Não há problemas de segurança óbvios
- [ ] O PR resolve o problema descrito

---

**Lembrete**: Este PR será automaticamente testado pelo CI. Certifique-se de que todos os checks passem antes de solicitar revisão.