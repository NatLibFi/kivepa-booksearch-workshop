// Function to fetch and display selected books
async function populateSelectedBooksTable(labels_set) {
    const response = await fetch('/' + labels_set + '/get_selected_books');
    const data = await response.json();

    const tableBody = document.querySelector('#selected-books-table-' + labels_set + ' tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    let rowNumber = 1; // Initialize the row number

    data.selectedBooks.forEach(book => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${rowNumber}</td>
            <td>${book.title}</td>
            <td>${book.authors}</td>
            <td>${book.labels_set}</td>
            <td>${book.search_count}</td>
        `;
        tableBody.appendChild(row);

        rowNumber++; // Increment the row number for the next row
    });
}
