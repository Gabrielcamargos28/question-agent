# Roteiro de Apresentação de Mestrado (UFU)
**Projeto:** Avaliação de LLMs como Assistentes de Codificação e Design Arquitetural  
**Estudo de Caso:** Agente de Integração PLURI  
**Tempo Estimado:** 5-7 minutos  

---

## Slide 1: Capa e Identificação
**Conteúdo Visual:**
*   **Título:** Co-autoria Arquitetural: Avaliando LLMs no Design e Construção de Sistemas Complexos.
*   **Subtítulo:** Um Estudo de Caso sobre a Estruturação Assistida do Agente PLURI.
*   **Autor:** Gabriel A. P. de Camargos.
*   **Instituição:** Mestrado em Ciência da Computação - IA (UFU).
*   **Disciplina:** Engenharia de Software Inteligente.

**Roteiro de Fala:**
"Bom dia a todos. Sou Gabriel Camargos e hoje vou apresentar meu projeto que investiga a transição do papel dos Large Language Models: de meros geradores de código para assistentes ativos no design arquitetural de software. O foco central não é apenas a extração de dados educacionais, mas sim como utilizamos o Gemini para projetar a arquitetura completa de um sistema, definindo sua modularidade e seus contratos de dados."

---

## Slide 2: O Tema: Engenharia de Software Assistida (AIE)
**Conteúdo Visual:**
*   **Evolução:** Do *Code Completion* (Snippets) ao *Software Design* (Sistemas).
*   **Foco:** Capacidade de modelagem, definição de padrões (Clean Architecture) e estruturação de módulos.
*   **Atuação da IA:** Projetista da infraestrutura e dos contratos de integração.

**Roteiro de Fala:**
"O tema central deste trabalho é a Engenharia de Software Assistida por IA. Investigamos como o LLM pode atuar como um 'Arquiteto', auxiliando na tomada de decisões arquiteturais. Diferente do uso comum para sugerir linhas isoladas, aqui provocamos a IA a propor a estrutura de pastas, a separação de responsabilidades e os padrões de integração que sustentam a aplicação."

---

## Slide 3: Problema e Questões de Pesquisa (RQs)
**Conteúdo Visual:**
*   **Problema:** O alto esforço cognitivo e o risco de débito técnico no design inicial de sistemas de integração complexos.
*   **Questões de Pesquisa:**
    *   **RQ1 (Design):** Em que medida o LLM facilita a estruturação de uma arquitetura modular e desacoplada?
    *   **RQ2 (Modelagem):** Qual a precisão da IA na criação de contratos de dados (Pydantic) para APIs de produção?
    *   **RQ3 (Refatoração):** Qual o esforço humano necessário para validar o design proposto pela IA?

**Roteiro de Fala:**
"Sabemos que Projetar sistemas de integração do zero exige muito tempo de modelagem. O problema que atacamos é o custo desse design inicial. As questões de pesquisa buscam medir se o LLM consegue propor arquiteturas resilientes e o quanto um desenvolvedor humano precisa intervir para tornar a proposta da IA pronta para produção, medindo esse esforço através de métricas de refatoração."

---

## Slide 4: Metodologia: O Ciclo de Design Assistido
**Conteúdo Visual:**
*   **Fluxo AI-Driven:**
    1.  **Briefing:** Entrada de requisitos de negócio.
    2.  **Arquitetura (IA):** Proposta de estrutura de módulos (FastAPI, LangChain).
    3.  **Contratos (IA):** Modelagem de Schemas Pydantic.
    4.  **Implementação:** Codificação assistida dos serviços.
*   **Exemplo de Prompt Arquitetural:** *"Refatore a estrutura de pastas para a mais utilizada em agentes"* (Extraído do log `all_prompts.md`).

**Roteiro de Fala:**
"Nossa metodologia inverteu o papel tradicional de desenvolvimento. O Gemini foi induzido a sugerir a organização da arquitetura. Ele propôs a divisão em módulos de serviços, modelos e núcleo, e definiu a stack tecnológica. Todo o processo foi auditado por logs de decisão, permitindo rastrear a 'lógica arquitetural' aplicada pelo modelo."

---

## Slide 5: Resultado: A Arquitetura Proposta pela IA
**Conteúdo Visual:**
*   **Design Modular:** Separação entre `document_parser`, `ai_extractor` e `api_client`.
*   **Contratos de Dados:** Uso de Pydantic como "Single Source of Truth".
*   **Observabilidade:** Sistema de logs e monitoramento de custos projetado pela própria IA.
*   **Agnosticismo:** Estrutura pronta para modelos locais (Ollama) ou nuvem (Gemini).

**Roteiro de Fala:**
"Em questão de resultados ate o momento foi uma arquitetura profissional e desacoplada. A IA propôs o uso de **Data Contracts** rigorosos via Pydantic, garantindo que a comunicação entre os módulos fosse tipada e segura. O design isola o parser de documentos da inteligência de extração, demonstrando que a IA é capaz de aplicar princípios de sênioridade, como a Responsabilidade Única (SRP), na estruturação do projeto."

---

## Slide 6: Estudo de Caso: Validando a Capacidade Técnica
**Conteúdo Visual:**
*   **Validação:** O Agente de Integração PLURI.
*   **Desafio Real:** Processamento de provas técnicas (Eletrônica/Informática) com imagens e tabelas.
*   **Sucesso:** Extração estruturada com 100% de aderência aos contratos arquiteturais.
*   **Métricas Operacionais (Flash-Lite):** 
    *   Detecção de Área: ~878 tokens (Custo: $0.000088)
    *   Extração JSON: ~3009 tokens (Custo: $0.000379)

**Roteiro de Fala:**
"Até o momento como prova de conceito, foi validado esse design no Agente PLURI. O sistema processou documentos reais e se integrou com sucesso à API da plataforma. O sucesso da extração é a evidência de que a arquitetura desenhada pela IA é funcional e suporta requisitos complexos de negócio. Além disso, a arquitetura provou ser financeiramente eficiente: nossos logs mostram que tarefas como a detecção de área custaram frações de um milésimo de centavo por execução usando modelos Flash-Lite, viabilizando o uso em larga escala."

---

## Slide 7: Conclusão e Resultados Esperados
**Conteúdo Visual:**
*   **Guia de Design Assistido por IA:** Metodologia para estruturação de sistemas.
*   **Framework de Arquitetura:** Modelagem de contratos e serviços via LLM.
*   **Validação de Eficácia:** Estudo de caso PLURI como prova de integridade.
*   **Impacto:** Redução do débito técnico e evolução do papel do desenvolvedor.

**Roteiro de Fala:**
"Para concluir, vem provando que os LLMs podem transcender a geração de simples de códigos para se tornarem **parceiros ativos no design arquitetural**. Esperamos entregar um framework que oriente desenvolvedores a utilizarem a IA para modelar sistemas inteiros. O sucesso do Agente PLURI valida que essa arquitetura projetada por IA é robusta e escalável, transformando o papel do desenvolvedor de um digitador de código em um **orquestrador de sistemas inteligentes**."

---

## 7. Detalhamento de Custos e Eficiência Operacional

Como parte da arquitetura assistida, o sistema implementa um módulo de monitoramento financeiro que permite auditar a viabilidade do projeto:

### 7.1. Tabela de Preços (Ref: Google Gemini)
*   **Gemini 2.0 Flash Lite:** \$0.075 / 1M tokens (Input) | \$0.30 / 1M tokens (Output)
*   **Gemini 1.5 Flash:** \$0.075 / 1M tokens (Input) | \$0.30 / 1M tokens (Output)
*   **Gemini 2.0 Flash:** \$0.10 / 1M tokens (Input) | \$0.40 / 1M tokens (Output)

### 7.2. Lógica de Cálculo de Tokens
O custo de cada operação é extraído dos metadados da resposta da IA e calculado via:
$$ \text{Custo} = \frac{(\text{Tokens In} \times \text{Preço In}) + (\text{Tokens Out} \times \text{Preço Out})}{1.000.000} $$

### 7.3. Registro de Auditoria
O projeto mantém um log persistente em `logs/costs.md`, detalhando cada transação por timestamp, tarefa e modelo, facilitando o cálculo do ROI (Retorno sobre Investimento) da automação.

