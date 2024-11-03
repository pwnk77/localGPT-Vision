'use client'

import * as React from 'react'
import { FileText, X } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { createEditor, Descendant, BaseEditor } from 'slate'
import { Slate, Editable, withReact, ReactEditor } from 'slate-react'
import { HistoryEditor, withHistory } from 'slate-history'

// Define custom types for Slate
type CustomEditor = BaseEditor & ReactEditor & HistoryEditor

type ParagraphElement = {
  type: 'paragraph'
  children: CustomText[]
}

type CustomElement = ParagraphElement

type CustomText = {
  text: string
  bold?: boolean
  italic?: boolean
  code?: boolean
}

// Augment the Slate types
declare module 'slate' {
  interface CustomTypes {
    Editor: CustomEditor
    Element: CustomElement
    Text: CustomText
  }
}

interface Tab {
  id: string
  title: string
  content: Descendant[]
}

interface EditorProps {
  activeTab: string
  openTabs: Tab[]
  onTabChange: (value: string) => void
  onTabClose: (tabId: string) => void
}

// Initial value for new editor instances
const initialValue: Descendant[] = [
  {
    type: 'paragraph',
    children: [{ text: '' }],
  },
]

export function Editor({ activeTab, openTabs, onTabChange, onTabClose }: EditorProps) {
  // Create a Slate editor object that won't change across renders
  const [editors] = React.useState<Record<string, CustomEditor>>(() => 
    openTabs.reduce((acc, tab) => ({
      ...acc,
      [tab.id]: withHistory(withReact(createEditor())),
    }), {})
  )

  return (
    <div className="flex h-full flex-col">
      <Tabs value={activeTab} onValueChange={onTabChange} className="flex-1">
        <TabsList className="w-full justify-start rounded-none border-b bg-background p-0">
          {openTabs.map((tab) => (
            <div key={tab.id} className="flex items-center">
              <TabsTrigger
                value={tab.id}
                className="relative rounded-none border-r data-[state=active]:bg-muted"
              >
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  {tab.title}
                </div>
              </TabsTrigger>
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 rounded-sm p-0 hover:bg-accent mx-2"
                onClick={() => onTabClose(tab.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </TabsList>
        {openTabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="h-full border-0 p-0">
            <div className="h-full rounded-lg border p-4">
              <Slate 
                editor={editors[tab.id]} 
                initialValue={tab.content || initialValue}
              >
                <Editable
                  className="h-full outline-none"
                  placeholder="Start typing..."
                />
              </Slate>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
