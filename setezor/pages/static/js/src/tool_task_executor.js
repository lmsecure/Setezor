async function executeToolTasks({ tasks, stopOnFirstFailure = true }) {
  const responses = [];

  for (const task of tasks) {
    try {
      let response = await fetch(task.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task.payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = errorData.detail || '';

        if (detail.includes('not able to perform this task') && detail.includes('Module name:')) {
          const moduleMatch = detail.match(/Module name:\s*(\w+)/);
          const moduleName = moduleMatch ? moduleMatch[1] : 'unknown';

          await window.moduleInstaller.prompt(task.payload.agent_id, moduleName);

          return { success: false, reason: 'module_install_requested' };
        }

        throw new Error(`HTTP ${response.status}: ${errorData.detail || ''}`);
      }

      responses.push(response);

    } catch (error) {
      console.error('Task failed:', error);
      if (stopOnFirstFailure) {
        return { success: false, error };
      }
    }
  }

  return { success: true, responses };
}

window.executeToolTasks = executeToolTasks;