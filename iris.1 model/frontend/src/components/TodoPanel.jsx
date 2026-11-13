import React, { useState, useEffect, useCallback } from 'react'
import { getTodos, createTodo, toggleTodo, deleteTodo, clearAllTodos } from '../api'

export default function TodoPanel({ onClose, onTaskReminder }) {
  const [todos, setTodos] = useState([])
  const [newTask, setNewTask] = useState('')
  const [remindPreset, setRemindPreset] = useState('none')
  const [loading, setLoading] = useState(false)

  const fetchTodos = useCallback(async () => {
    try {
      const data = await getTodos()
      if (data && Array.isArray(data.todos)) {
        setTodos(data.todos)
      }
    } catch (e) {
      console.error('Failed to fetch todos:', e)
    }
  }, [])

  useEffect(() => {
    fetchTodos()
    const interval = setInterval(fetchTodos, 4000)
    return () => clearInterval(interval)
  }, [fetchTodos])

  const handleAdd = async (e) => {
    e?.preventDefault()
    const task = newTask.trim()
    if (!task) return

    let remindSec = null
    if (remindPreset === '1m') remindSec = 60
    else if (remindPreset === '5m') remindSec = 300
    else if (remindPreset === '15m') remindSec = 900
    else if (remindPreset === '1h') remindSec = 3600

    setLoading(true)
    try {
      await createTodo(task, remindSec)
      setNewTask('')
      setRemindPreset('none')
      await fetchTodos()
    } catch (err) {
      console.error('Error adding todo:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (todoId, currentStatus) => {
    try {
      await toggleTodo(todoId, !currentStatus)
      setTodos(prev => prev.map(t => t.id === todoId ? { ...t, completed: !currentStatus } : t))
    } catch (err) {
      console.error('Error toggling todo:', err)
    }
  }

  const handleDelete = async (todoId) => {
    try {
      await deleteTodo(todoId)
      setTodos(prev => prev.filter(t => t.id !== todoId))
    } catch (err) {
      console.error('Error deleting todo:', err)
    }
  }

  const handleClearAll = async () => {
    if (todos.length === 0) return
    if (window.confirm('Wipe all tasks from Layer 2 memory and start fresh?')) {
      setLoading(true)
      try {
        await clearAllTodos()
        setTodos([])
      } catch (err) {
        console.error('Error clearing todos:', err)
      } finally {
        setLoading(false)
      }
    }
  }

  const formatReminder = (remindAt) => {
    if (!remindAt) return null
    const diffSec = Math.round((remindAt - (Date.now() / 1000)))
    if (diffSec <= 0) return '🔔 Due now'
    if (diffSec < 60) return `🔔 In ${diffSec}s`
    const mins = Math.round(diffSec / 60)
    if (mins < 60) return `🔔 In ${mins}m`
    const hrs = Math.round(mins / 60)
    return `🔔 In ${hrs}h`
  }

  const pendingCount = todos.filter(t => !t.completed).length

  return (
    <div className="todo-panel">
      <div className="todo-panel-header">
        <div className="todo-title-group">
          <span className="todo-icon">📋</span>
          <h3>Tasks & Reminders</h3>
          <span className="todo-badge">{pendingCount} pending</span>
        </div>
        <div className="todo-header-actions">
          <span className="todo-memory-layer" title="Stored in IRIS 2nd Memory Layer (18-Day LongTempLayer)">
            Layer 2 Memory
          </span>
          <button
            type="button"
            className="todo-clear-all-btn"
            onClick={handleClearAll}
            title="Clear all tasks from Layer 2 memory and start fresh"
          >
            🧹 Clear All
          </button>
          {onClose && (
            <button type="button" className="todo-close-btn" onClick={onClose}>
              ✕
            </button>
          )}
        </div>
      </div>

      <form className="todo-add-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Add a new task (e.g. Call client, review pull request)..."
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          className="todo-input"
        />
        <div className="todo-form-bottom">
          <select
            value={remindPreset}
            onChange={(e) => setRemindPreset(e.target.value)}
            className="todo-remind-select"
          >
            <option value="none">No reminder</option>
            <option value="1m">Remind in 1 min</option>
            <option value="5m">Remind in 5 mins</option>
            <option value="15m">Remind in 15 mins</option>
            <option value="1h">Remind in 1 hour</option>
          </select>
          <button type="submit" className="todo-add-btn" disabled={loading || !newTask.trim()}>
            + Add Task
          </button>
        </div>
      </form>

      <div className="todo-list">
        {todos.length === 0 ? (
          <div className="todo-empty">
            <p>No tasks yet.</p>
            <p className="todo-empty-hint">Say <em>"make a to do list..."</em> or type a task above.</p>
          </div>
        ) : (
          todos.map(todo => (
            <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <label className="todo-checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => handleToggle(todo.id, todo.completed)}
                />
                <span className="todo-checkmark" />
              </label>
              <div className="todo-content">
                <span className="todo-text">{todo.task}</span>
                {todo.remind_at && (
                  <span className={`todo-reminder-tag ${todo.reminded ? 'reminded' : ''}`}>
                    {todo.reminded ? '✓ Reminded' : formatReminder(todo.remind_at)}
                  </span>
                )}
              </div>
              <button
                type="button"
                className="todo-delete-btn"
                onClick={() => handleDelete(todo.id)}
                title="Delete task"
              >
                🗑
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
