'use client'

import * as React from 'react'
import { FileText, X } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'

interface Tab {
  id: string
  title: string
}

interface EditorProps {
  activeTab: string
  openTabs: Tab[]
  onTabChange: (value: string) => void
  onTabClose: (tabId: string) => void
}

export function Editor({ activeTab, openTabs, onTabChange, onTabClose }: EditorProps) {
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
              <div className="text-sm text-muted-foreground">
                editor content for {tab.title}
              </div>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
