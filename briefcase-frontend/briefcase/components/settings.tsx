'use client'

import * as React from 'react'
import { useState } from 'react'

interface SettingsFormData {
  indexerModel: string
  generationModel: string
  resizedHeight: number
  resizedWidth: number
}

export function Settings() {
  const [settings, setSettings] = useState<SettingsFormData>({
    indexerModel: 'vidore/colpali',
    generationModel: 'qwen',
    resizedHeight: 224,
    resizedWidth: 224,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Settings saved:', settings)
  }

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target
    setSettings(prev => ({
      ...prev,
      [name]: value
    }))
  }

  return (
    <div className="p-4">
      <h2 className="text-base font-medium mb-4">Settings</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="border border-gray-700 rounded-lg p-4 bg-gray-900">
          <h2 className="text-sm font-medium mb-3 text-gray-200">Vision Model Settings</h2>
          
          {/* Retrieval Model Section */}
          <div>
            <h3 className="text-xs font-medium mb-2 text-gray-300">Retrieval Model</h3>
            <div className="mb-3">
              <label htmlFor="indexerModel" className="block text-xs mb-1 text-gray-300">
                Select Indexer Model:
              </label>
              <select
                id="indexerModel"
                name="indexerModel"
                value={settings.indexerModel}
                onChange={handleChange}
                className="w-full p-1.5 text-xs rounded-md bg-gray-800 border border-gray-700 text-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="vidore/colpali">vidore/colpali</option>
                <option value="vidore/colpali-v1.2">vidore/colpali-v1.2</option>
                <option value="vidore/colqwen2-v0.1">vidore/colqwen2-v0.1</option>
              </select>
            </div>
          </div>

          <div className="border-t border-gray-700 my-4"></div>

          {/* Generation Model Section */}
          <div>
            <h3 className="text-xs font-medium mb-2 text-gray-300">Generation Model</h3>
            <div className="mb-3">
              <label htmlFor="generationModel" className="block text-xs mb-1 text-gray-300">
                Select Generation Model:
              </label>
              <select
                id="generationModel"
                name="generationModel"
                value={settings.generationModel}
                onChange={handleChange}
                className="w-full p-1.5 text-xs rounded-md bg-gray-800 border border-gray-700 text-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="qwen">Qwen2-VL-7B-Instruct</option>
                <option value="gemini">Google Gemini</option>
                <option value="gpt4">OpenAI GPT-4</option>
                <option value="llama-vision">Llama-Vision</option>
                <option value="pixtral">Pixtral</option>
                <option value="molmo">Molmo</option>
                <option value="groq-llama-vision">Groq Llama Vision</option>
              </select>
            </div>
          </div>

          <div className="border-t border-gray-700 my-4"></div>

          {/* Image Settings Section */}
          <div>
            <h3 className="text-xs font-medium mb-2 text-gray-300">Image Settings</h3>
            <div className="space-y-3">
              <div>
                <label htmlFor="resizedHeight" className="block text-xs mb-1 text-gray-300">
                  Image Resized Height (multiple of 28):
                </label>
                <input
                  type="number"
                  id="resizedHeight"
                  name="resizedHeight"
                  value={settings.resizedHeight}
                  onChange={handleChange}
                  min={28}
                  step={28}
                  className="w-full p-1.5 text-xs rounded-md bg-gray-800 border border-gray-700 text-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label htmlFor="resizedWidth" className="block text-xs mb-1 text-gray-300">
                  Image Resized Width (multiple of 28):
                </label>
                <input
                  type="number"
                  id="resizedWidth"
                  name="resizedWidth"
                  value={settings.resizedWidth}
                  onChange={handleChange}
                  min={28}
                  step={28}
                  className="w-full p-1.5 text-xs rounded-md bg-gray-800 border border-gray-700 text-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="bg-blue-600 text-xs text-white px-3 py-1.5 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
        >
          Save Settings
        </button>
      </form>
    </div>
  )
}
