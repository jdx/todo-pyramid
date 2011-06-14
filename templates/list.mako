<%inherit file="layout.mako"/>

<h1>Todo List</h1>

<ul id="todos">
% if todos:
  % for todo in todos:
  <li>
    <span class="name">${todo['name']}</span>
    <span class="actions">
      [ <a href="${request.route_url('close', id=todo['id'])}">close</a> ]
    </span>
  </li>
  % endfor
% else:
  <li>There are no open todos</li>
% endif
  <li class="last">
    <a href="${request.route_url('new')}">Add a new todo</a>
  </li>
</ul>
