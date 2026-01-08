
import { GoogleGenAI, Type } from "@google/genai";

const getAIClient = () => {
  return new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
};

export const runUIAutomator = async (instruction: string) => {
  const ai = getAIClient();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: `Simulate a browser-use agent task. Given this instruction: "${instruction}", return a JSON object describing the step-by-step execution plan and a final summary.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          steps: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                action: { type: Type.STRING },
                status: { type: Type.STRING, enum: ['done', 'failed'] }
              },
              required: ['action', 'status']
            }
          },
          summary: { type: Type.STRING }
        },
        required: ['steps', 'summary']
      }
    }
  });

  return JSON.parse(response.text || '{}');
};

export const profileData = async (fileName: string, sampleData: string) => {
  const ai = getAIClient();
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: `Analyze this data sample from file "${fileName}":\n\n${sampleData}\n\nProvide a data profile report in JSON format including basic stats, AI-driven insights, and potential anomalies.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          stats: {
            type: Type.OBJECT,
            properties: {
              rows: { type: Type.NUMBER },
              columns: { type: Type.NUMBER },
              missingValues: { type: Type.NUMBER },
              duplicateRows: { type: Type.NUMBER }
            },
            required: ['rows', 'columns', 'missingValues', 'duplicateRows']
          },
          insights: {
            type: Type.ARRAY,
            items: { type: Type.STRING }
          },
          anomalies: {
            type: Type.ARRAY,
            items: { type: Type.STRING }
          }
        },
        required: ['stats', 'insights', 'anomalies']
      }
    }
  });

  return JSON.parse(response.text || '{}');
};

export const checkDataQuality = async (data: string, rules: string) => {
  const ai = getAIClient();
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: `Apply these quality rules: "${rules}" to this dataset snippet: "${data}". List all violations and suggestions.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          violations: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                rule: { type: Type.STRING },
                issue: { type: Type.STRING },
                severity: { type: Type.STRING, enum: ['low', 'medium', 'high'] }
              },
              required: ['rule', 'issue', 'severity']
            }
          },
          score: { type: Type.NUMBER, description: 'Quality score from 0-100' }
        },
        required: ['violations', 'score']
      }
    }
  });

  return JSON.parse(response.text || '{}');
};
