'use client'

import * as React from 'react'
import { Send } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export function Assistant() {
  return (
    <Card className="flex h-full flex-col rounded-none border-0 bg-transparent">
      <CardHeader>
        <CardTitle className="text-lg font-medium">document assistant</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <ScrollArea className="h-[calc(100vh-14rem)]">
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              how can i help you today?
            </div>
          </div>
        </ScrollArea>
      </CardContent>
      <div className="p-4">
        <div className="flex gap-2">
          <Input placeholder="type your message..." className="flex-1" />
          <Button size="icon"><Send className="h-4 w-4" /></Button>
        </div>
      </div>
    </Card>
  )
}
