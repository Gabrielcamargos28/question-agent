# Proposta de Artigo e Roteiro de Apresentação (Versão 2.2)

**Disciplina:** Engenharia de Software Inteligente - Mestrado em Ciência da Computação (UFU)  
**Projeto:** Avaliação de LLMs como Assistentes de Codificação e Design Arquitetural  
**Estudo de Caso:** Agente de Integração PLURI (Extração de Questões)  
**Autor:** Gabriel Camargos  

---

## 1. Tema
**Título:** Avaliação de LLMs como Assistentes de Codificação e Design Arquitetural: Um Estudo de Caso na Construção da Plataforma PLURI.()

Este trabalho investiga o papel dos Large Language Models (LLMs) não apenas como executores de tarefas, mas como assistentes no ciclo de vida de desenvolvimento de software. O estudo de caso foca na construção de um agente inteligente para extração de dados educacionais, analisando como o LLM auxiliou na modelagem da arquitetura, na definição de schemas via Pydantic e na implementação de parsers complexos.

---

## 2. Problema e Questões de Pesquisa (RQs)

**Problema:** Desenvolver pipelines de processamento de documentos e integrações sistêmicas do zero exige um alto esforço cognitivo. O desafio é entender como os LLMs podem mitigar esse esforço na fase de codificação e design, garantindo qualidade arquitetural.

### Questões de Pesquisa:
*   **RQ1 (Eficácia na Geração de Código):** Como diferentes modelos (Gemini 1.5 Pro vs. Flash) se comportam na geração de módulos de parsing e integração que atendam a requisitos de negócio reais?
*   **RQ2 (Design e Modelagem):** Em que medida o uso de LLMs facilita a definição de contratos de dados (schemas Pydantic) e a estruturação de uma arquitetura modular?
*   **RQ3 (Qualidade e Refatoração):** Qual o nível de intervenção humana e refatoração necessário para tornar o código gerado pelo LLM "pronto para produção"?
*   **RQ4 (Técnicas de Prompting):** Como a transição de Zero-shot para Few-shot impacta a robustez do código de extração gerado?

---

## 3. Metodologia e Método de Avaliação

### 3.1. Método de Desenvolvimento Assistido
O desenvolvimento do agente seguiu um fluxo iterativo documentado em logs:
1.  **Arquitetura Inicial:** Definição assistida dos módulos `ai_extractor.py`, `document_parser.py` e `api_client.py`.
2.  **Prompt Engineering:** Aplicação de instruções para gerar a lógica de extração baseada em Pydantic.
3.  **Ciclo de Feedback:** Identificação de falhas (ex: erros 500 ou extrações incompletas documentadas nos logs) e uso do LLM para sugerir correções no código.

### 3.2. Métricas de Avaliação de Software
Para avaliar o auxílio do LLM na Engenharia de Software, utilizaremos:
*   **Aderência ao Requisito (Functional Correctness):** Percentual de funções geradas que passam nos testes de integração com a API PLURI.
*   **Esforço de Refatoração (Edit Distance):** Medição da quantidade de alterações manuais necessárias no código gerado pelo LLM.
*   **Complexidade Ciclomática:** Análise da simplicidade e manutenibilidade do código gerado (comparando Pro vs. Flash).
*   **Densidade de Erros de Integração:** Quantidade de falhas de contrato (Pydantic Validation Errors) encontradas durante o desenvolvimento.

---

## 4. Desenho Experimental (Setup)
*   **Modelos Testados:** Gemini 1.5 Pro e Gemini 2.5 Flash.
*   **Ambiente de Desenvolvimento:** Pycharm, Python 3.11, Pydantic.
*   **Estudo de Caso Prático:** Implementação do pipeline que processa o arquivo `prova-pluri-ELE-2.pdf`, validando se o código gerado pelo LLM lidou corretamente com a complexidade do documento (imagens e tabelas).

---

## 5. Resultados Esperados
*   **Guia de Design Assistido:** Documentação de como estruturar prompts para gerar arquiteturas de integração robustas.
*   **Comparativo de Modelos para Devs:** Análise de qual modelo oferece o melhor suporte para tarefas de codificação e refatoração.
*   **Validação do Estudo de Caso:** Um sistema funcional onde a maior parte da lógica de integração e parsing foi co-autorada por LLMs.

---

# ROTEIRO DE APRESENTAÇÃO - SLIDES (5 MINUTOS)

## Slide 1: Capa e Identificação (30s)
**Roteiro:** "Bom dia. Sou Gabriel Camargos e hoje vou apresentar o meu pré-projeto sobre o papel dos LLMs como assistentes no ciclo de vida de desenvolvimento de software e arquitetural. A ideia é analisar como a IA impacta o design e a implementação de um sistema até a produção."
## Slide 1: Tema (30s)
O tema central da pesquisa é a Engenharia de Software Assistida por IA. O objetivo é investigar a transição do uso de LLMs: avaliár os modelos como assistentes ativos no design arquitetural e na modelagem de contratos em sistemas complexos com a menor intervenção possível. Para validar essa tese, a ideia é utilizar o estudo de caso a construção do Agente de Integração da plataforma PLURI. Falar rapidamente sobre o Pluri...

## Slide 2: O Problema e o Contexto (45s)
**Roteiro:** "Desenvolver integrações do zero exige muito esforço em modelagem e contratos de dados de apis. O desafio não é apenas usar a IA para extrair dados, mas sim entender como ela pode reduzir o débito técnico e o esforço de codificação durante a construção de sistemas complexos de parsing e integração."

## Slide 3: Questões de Pesquisa (RQs) (45s)
**Roteiro:** "Nossas RQs focam em quatro pilares: a comparação entre os modelos Pro e Flash, a eficácia na definição de contratos de dados via Pydantic, o esforço real de refatoração humana necessário e como a evolução do prompting altera a qualidade do código entregue."

## Slide 4: Metodologia: Ciclo Assistido (45s)
**Roteiro:** "Na metodologia eu pretendo seguir um fluxo iterativo documentado. Começamdo pela definição assistida da arquitetura modular, passamos pela geração de código via prompts estruturados e fechamos o ciclo usando a própria IA para diagnosticar e corrigir falhas apontadas pelos nossos logs de execução. Implementar a geração de logs de custos por iteração."

## Slide 5: Métricas de Engenharia de Software (45s)
**Roteiro:** "Para medir o auxílio da IA de forma objetiva, pretendo utilizar métricas de engenharia: aderência aos requisitos funcionais, o esforço de refatoração medido pela distância de edição do código e a análise da complexidade e manutenibilidade dos módulos gerados pelos modelos Pro e Flash. E realização de testes de integração entre o agente e a API da plataforma"

## Slide 6: Estudo de Caso: O Agente PLURI (45s)
**Roteiro:** "No nosso estudo prático, implementamos o pipeline para processar documentos técnicos complexos. Analisamos como cada modelo lidou com a estrutura de imagens e tabelas, validando se o código gerado foi capaz de manter a integridade do contrato de dados exigido pela nossa API existente dentro da Plataforma do pluri"

## Slide 7: Conclusão e Resultados Esperados (30s)
**Roteiro:** "Esperamos entregar um guia prático de design assistido e provar que, com a estratégia de prompting correta, os LLMs não apenas escrevem código, mas ajudam a estruturar sistemas mais robustos e modulares, acelerando significativamente a entrega."

---

## 6. Estimativa de Custos do Projeto

A viabilidade financeira e o monitoramento de recursos do projeto são realizados através de um sistema de rastreamento de custos em tempo real, integrado diretamente no pipeline de execução do agente.

### 3.1. Modelo de Precificação
Os custos são calculados com base no consumo de tokens (entrada e saída) utilizando os valores de mercado para as APIs do Google Gemini (preço por 1 milhão de tokens):
*   **Gemini 1.5 Flash:** \$0.075 (entrada) / \$0.30 (saída)
*   **Gemini 2.0 Flash:** \$0.10 (entrada) / \$0.40 (saída)
*   **Gemini 2.0 Flash Lite:** \$0.075 (entrada) / \$0.30 (saída)

### 3.2. Metodologia de Cálculo
Para cada tarefa realizada pelo agente (detecção de área, extração de questões, correções), o sistema captura o metadado de uso e aplica a fórmula:
$$ \text{Custo Total} = \left( \frac{\text{Tokens de Entrada}}{10^6} \times \text{Preço In} \right) + \left( \frac{\text{Tokens de Saída}}{10^6} \times \text{Preço Out} \right) $$

### 3.3. Transparência e Auditoria
Todos os gastos são auditados no arquivo `logs/costs.md`, permitindo uma análise comparativa entre modelos (ex: custo-benefício do Flash vs Pro) e a identificação de gargalos de eficiência nos prompts desenvolvidos.

