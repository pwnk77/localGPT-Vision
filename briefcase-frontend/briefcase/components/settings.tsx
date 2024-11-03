'use client'

import * as React from 'react'
import { useState, useEffect } from 'react'
import { toast } from 'sonner'

interface SettingsFormData {
  indexerModel: string
  generationModel: string
  resizedHeight: number
  resizedWidth: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function Settings() {
  const [settings, setSettings] = useState<SettingsFormData>({
    indexerModel: 'vidore/colpali',
    generationModel: 'qwen',
    resizedHeight: 280,
    resizedWidth: 280,
  })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch(`${API_URL}/api/settings`, {
          headers: {
            'Content-Type': 'application/json',
          },
        })
        
        if (!response.ok) throw new Error('Failed to fetch settings')
        
        const data = await response.json()
        setSettings({
          indexerModel: data.indexer_model,
          generationModel: data.generation_model,
          resizedHeight: data.resized_height,
          resizedWidth: data.resized_width,
        })
      } catch (error) {
        console.error('Error fetching settings:', error)
        toast.error('Failed to load settings')
      }
    }

    fetchSettings()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          indexer_model: settings.indexerModel,
          generation_model: settings.generationModel,
          resized_height: settings.resizedHeight,
          resized_width: settings.resizedWidth,
        }),
      })

      if (!response.ok) throw new Error('Failed to update settings')
      
      toast.success('Settings saved successfully')
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error('Failed to save settings')
    } finally {
      setIsLoading(false)
    }
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
          disabled={isLoading}
          className={`bg-blue-600 text-xs text-white px-3 py-1.5 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isLoading ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}
