async function generateBooksTable() {
    try {
        const response = await fetch('/searched_books');
        const data = await response.json();

        const table = $('#books-table');
        table.empty(); // Clear existing rows

        // Generate and insert the table head
        const tableHead = $('<thead>').html(`
            <tr>
                <th>#</th>
                <th>Title</th>
                <th>Author(s)</th>
                <th>Is found</th>
            </tr>
        `);
        table.append(tableHead);

        let rowNumber = 1; // Initialize the row number

        data.searchedBooks.forEach(book => {
            const row = $('<tr>');
            row.html(`
                <td>${rowNumber}</td>
                <td>${book.title}</td>
                <td>${book.authors}</td>
                <td>${book.is_found}</td>
            `);
            table.append(row);

            rowNumber++; // Increment the row number for the next row
        });
    } catch (error) {
        console.error('Error fetching selected books:', error);
    }
}
