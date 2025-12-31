# Testes Outputs

## Testando: Health Check

✅ PASS (HTTP 200)
Response:

```json
{
  "status": "healthy",
  "ollama_status": "healthy",
  "documents_indexed": 81,
  "embedding_model": "all-MiniLM-L6-v2",
  "timestamp": "2025-12-31T00:34:33.723567"
}
```

---

## Testando: Pergunta Válida

✅ PASS (HTTP 200)
Response:

```json
{
  "answer": "[AVISO: Resposta pode não estar totalmente baseada nos documentos]\n\nDe acordo com o contrato, as responsabilidades dos locatários e dos locadores são as seguintes:\n\n13.1 Reparos Urgentes de Responsabilidade do Locador:\n\n* When there is a lack of habitability due to serious leaks or infiltrations, it is understood that an urgent repair is necessary. In this case, the Locator must respond within 3 days of receiving the notification on the procedure to be adopted for the repair.\n\n13.2 Reparos Emergenciais de Responsabilidade do Locador:\n\n* When there is a serious violation of the building's structure or integrity, it is understood that an emergency repair is necessary. The Locator must respond within 3 days of receiving the notification on the procedure to be adopted for the repair.\n\n16 Responsabilidade das Partes:\n\n* Both the Tenant and the Locator must guarantee the veracity and update of their respective personal data transmitted to QuintoAndar for the execution of this Contract.\n\nTherefore, the Locator is responsible for responding to notifications of urgent or emergency repairs within the established timeframes, and both parties are responsible for ensuring the accuracy and updating of their personal data.",
  "citations": [
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "Locador deverá \nresponder no prazo de 7 dias, da ciência da existência do vício, a \nprovidência a ser adotada\npara realização do reparo. Se o Locador não se \nmanifestar no prazo estabelecido, aplicam-se integralmente\nao presente \nContrato as disposições conforme disposto em \n\"\nquin.to/regras-locacao...",
      "page": 3,
      "score": 0.694
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "as condições de usabilidade do imóvel \nmas não o tornam inabitável, tais como vazamentos ou\ninfiltrações graves, \nentende-se que é necessário um reparo urgente. Neste caso, o Locador deverá\nresponder sobre o procedimento a ser adotado para a realização do reparo \nem até 3 dias, contados do\nrecebimen...",
      "page": 3,
      "score": 0.6865
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "compartilhados com terceiros para \nque seja possível a execução do presente Contrato e que tal\ncompartilhamento ocorrerá em observância aos \nprincípios e obrigações trazidos pela LGPD.\n16. Responsabilidade das Partes: \nInquilino e Locador deverão garantir a veracidade e a atualização dos\nseus respec...",
      "page": 3,
      "score": 0.6584
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "e intimações. Caso o Inquilino\nreceba qualquer comunicação emitida \nrelacionada ao imóvel, deverá encaminhar \nà \nAdministradora\n, \nsob\npena de ser responsabilizado pelos prejuízos decorrentes da omissão \nde envio da Notificação.\n24. Múltiplas Partes: \nHavendo mais de um Locador e/ou Inquilino, todos...",
      "page": 5,
      "score": 0.6531
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "realize, \nde acordo com os prazos do item 13.\n12. Danos causados durante a Locação: \nO Inquilino deverá reparar prontamente os danos causados ao\nImóvel, \nàs suas instalações ou a bens móveis e acessórios, desde que ocasionados \npelo Inquilino, demais\nmoradores, familiares ou visitantes, \nindependent...",
      "page": 3,
      "score": 0.6518
    }
  ],
  "metrics": {
    "total_latency_ms": 62761.37,
    "retrieval_latency_ms": 9.15,
    "llm_latency_ms": 62749.75,
    "prompt_tokens": 374,
    "completion_tokens": 289,
    "total_tokens": 663,
    "estimated_cost_usd": 0.0,
    "top_k_used": 5,
    "context_size": 2231,
    "groundedness_score": 0.141,
    "timestamp": "2025-12-31T00:35:36.493416"
  },
  "status": "success"
}
```

---

## Testando: Prompt Injection (deve bloquear)

❌ FAIL (HTTP 400)
Response:

```json
{
  "detail": {
    "error": "query_blocked",
    "violation": {
      "blocked": true,
      "reason": "Prompt injection attempt detected",
      "policy": "INJECTION_PREVENTION_POLICY",
      "message": "Sua pergunta contém padrões que violam nossas políticas de segurança. Por favor, reformule sua pergunta."
    }
  }
}
```

---

## Testando: Dados Sensíveis (deve bloquear)

❌ FAIL (HTTP 400)
Response:

```json
{
  "detail": {
    "error": "query_blocked",
    "violation": {
      "blocked": true,
      "reason": "Request for sensitive or out-of-domain information",
      "policy": "DOMAIN_RESTRICTION_POLICY",
      "message": "Sua pergunta solicita informações sensíveis ou fora do domínio dos documentos disponíveis. Não posso fornecer esse tipo de informação."
    }
  }
}
```

---

## Testando: Query Fora do Domínio

✅ PASS (HTTP 200)
Response:

```json
{
  "answer": "[AVISO: Resposta pode não estar totalmente baseada nos documentos]\n\nPara responder à pergunta \"Qual é a capital da França?\", precisamos utilizar as informações fornecidas nos documentos.\n\nO documento [template_pull_request.pdf, página 1] não fornece informações sobre a capital da França.\n\nNo documento [5Andar_contrato.pdf, página 7], podemos ver que a autorização de entrada é para um imóvel localizado em Taboão da Serra, SP, CEP: 06764-290. Neste caso, a capital da França não é relevante para a situação descrita no documento.\n\nPortanto, a resposta à pergunta \"Qual é a capital da França?\" é que não há informações relevantes sobre essa questão nos documentos fornecidos.",
  "citations": [
    {
      "source": "template_pull_request.pdf",
      "excerpt": "----------------------------------------\n \n \n##\n \nContexto\n \n-\n \nResuma\n \nem\n \n2–3\n \nlinhas\n \no\n \nproblema\n \nou\n \nnecessidade\n \nque\n \neste\n \nPR\n \nresolve\n \n \n----------------------------------------\n \n \n##\n \nO\n \nque\n \nfoi\n \nfeito\n \n-\n \nListe\n \nas\n \nprincipais\n \nmudanças\n \ndeste\n \nPR\n \n \n------------...",
      "page": 1,
      "score": 0.4483
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "Autorização de Entrada\nAo responsável pelo condomínio,\nNa qualidade de intermediadora da locação do referido imóvel, autorizamos a entrada dos \nlocatários abaixo, a\nser realizada a partir da data de vigência acordada no quadro resumo do Contrato de Locação.\nImóvel:\nApartamento \nAp 244 Torre 02, \nloc...",
      "page": 7,
      "score": 0.433
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "Contrato: v12.1_01/2023, nº 1215972_475478L\nContrato de Locação Residencial\nImóvel:\n \nApartamento Ap 244 Torre 02, localizado à Estrada São Francisco, no. 1588, Jardim Henriqueta,\nTaboão da Serra - SP, CEP: 06764-290\n, código QuintoAndar, \n893915972\n, que \ntem fim exclusivamente\nresidencial.\nAluguel...",
      "page": 1,
      "score": 0.4147
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "as assinaturas eletrônicas do presente \nContrato, por meio de plataformas de assinatura eletrônica,\ndevidamente autorizadas pela Infraestrutura de Chaves \nPúblicas Brasileira – ICP-Brasil (e.g., Docusign), serão\nconsideradas válidas, sendo o Contrato considerado executável, \nválido e vigente entre a...",
      "page": 5,
      "score": 0.3852
    },
    {
      "source": "5Andar_contrato.pdf",
      "excerpt": "IPTU:\n \nR$ 170 (cento e setenta reais) por mês\nSeguro Contra Incêndio:\n \nR$ 30 (trinta reais) por\nmês\nVaga de Garagem:\n \n2\nPrazo da Locação:\n \no Contrato terá prazo de 30 meses, \niniciado no dia ( \n08/02/2023 ) \ne com fim em (\n08/08/2025 )\nPrimeiro Pagamento:\n \n13/02/2023 \nApós o Primeiro Pagamento,...",
      "page": 1,
      "score": 0.3768
    }
  ],
  "metrics": {
    "total_latency_ms": 41531.24,
    "retrieval_latency_ms": 11.39,
    "llm_latency_ms": 41518.78,
    "prompt_tokens": 351,
    "completion_tokens": 152,
    "total_tokens": 503,
    "estimated_cost_usd": 0.0,
    "top_k_used": 5,
    "context_size": 2133,
    "groundedness_score": 0.2,
    "timestamp": "2025-12-31T00:36:18.046436"
  },
  "status": "success"
}
```

---

## Testando: Métricas

✅ PASS (HTTP 200)
Response:

```json
{
  "statistics": {
    "total_requests": 4,
    "blocked_requests": 2,
    "success_requests": 2,
    "block_rate": 0.5,
    "avg_latency_ms": 52146.308064460754,
    "p50_latency_ms": 62761.37399673462,
    "p95_latency_ms": 62761.37399673462,
    "p99_latency_ms": 62761.37399673462,
    "avg_retrieval_latency_ms": 10.269761085510254,
    "avg_llm_latency_ms": 52134.265422821045,
    "avg_tokens": 583.0,
    "total_tokens": 1166
  },
  "recent_requests": [
    {
      "timestamp": "2025-12-31T00:35:36.493424",
      "query_length": 53,
      "answer_length": 1227,
      "total_latency_ms": 62761.37399673462,
      "retrieval_latency_ms": 9.15384292602539,
      "llm_latency_ms": 62749.75109100342,
      "prompt_tokens": 374,
      "completion_tokens": 289,
      "total_tokens": 663,
      "top_k": 5,
      "context_size": 2231,
      "citations_count": 5,
      "blocked": false,
      "blocked_reason": null
    },
    {
      "timestamp": "2025-12-31T00:35:36.500745",
      "query_length": 57,
      "answer_length": 0,
      "total_latency_ms": 0.2720355987548828,
      "retrieval_latency_ms": 0,
      "llm_latency_ms": 0,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0,
      "top_k": 5,
      "context_size": 0,
      "citations_count": 0,
      "blocked": true,
      "blocked_reason": "INJECTION_PREVENTION_POLICY"
    },
    {
      "timestamp": "2025-12-31T00:35:36.508181",
      "query_length": 45,
      "answer_length": 0,
      "total_latency_ms": 0.29969215393066406,
      "retrieval_latency_ms": 0,
      "llm_latency_ms": 0,
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "total_tokens": 0,
      "top_k": 5,
      "context_size": 0,
      "citations_count": 0,
      "blocked": true,
      "blocked_reason": "DOMAIN_RESTRICTION_POLICY"
    },
    {
      "timestamp": "2025-12-31T00:36:18.046443",
      "query_length": 27,
      "answer_length": 676,
      "total_latency_ms": 41531.24213218689,
      "retrieval_latency_ms": 11.385679244995117,
      "llm_latency_ms": 41518.77975463867,
      "prompt_tokens": 351,
      "completion_tokens": 152,
      "total_tokens": 503,
      "top_k": 5,
      "context_size": 2133,
      "citations_count": 5,
      "blocked": false,
      "blocked_reason": null
    }
  ],
  "timestamp": "2025-12-31T00:36:18.053555"
}
```

---

=== Testes Completos ===
